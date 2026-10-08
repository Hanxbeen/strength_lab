import Foundation
import AuthenticationServices
import CryptoKit
import Security
import Combine

enum CloudConfiguration {
    static let url = URL(string: "https://gttvyfeyrnuspnnphuzk.supabase.co")!
    // Publishable keys are intended for public clients. Never ship service_role or secret keys.
    static let publishableKey = "sb_publishable_ghbVxjHXJQDYh7CbvA-y5A_5qhNpSIv"
}

struct CloudSession: Codable {
    let access_token: String
    let refresh_token: String
    let expires_at: Int?
    let expires_in: Int?
    let user: CloudUser
}
struct CloudUser: Codable {
    let id: UUID
}

enum CloudAuthError: LocalizedError {
    case invalidAppleToken, invalidNonce, expired, server
    var errorDescription: String? {
        switch self {
        case .invalidAppleToken: return "Apple 로그인 인증값을 읽지 못했습니다."
        case .invalidNonce: return "Apple 로그인 검증값이 일치하지 않습니다."
        case .expired: return "세션이 만료되었습니다. 다시 로그인해주세요."
        case .server: return "인증 서버 응답을 확인하지 못했습니다."
        }
    }
}

/// Keychain-backed session. Cloud upload is never automatic without user action.
@MainActor
final class CloudAuth: ObservableObject {
    @Published private(set) var userID: UUID?
    @Published private(set) var error: String?
    private var session: CloudSession?
    private var nonce: String?
    private let keychainAccount = "strength_lab.supabase.session"

    init() {
        if let data = readKeychain(),
           let saved = try? JSONDecoder().decode(CloudSession.self, from: data) {
            session = saved
            userID = saved.user.id
        }
    }

    func makeAppleRequest(_ request: ASAuthorizationAppleIDRequest) {
        let raw = UUID().uuidString + UUID().uuidString
        nonce = raw
        let digest = SHA256.hash(data: Data(raw.utf8))
        request.requestedScopes = [.email]
        request.nonce = digest.map { String(format: "%02x", $0) }.joined()
    }

    func finishAppleSignIn(_ result: Result<ASAuthorization, Error>) async {
        do {
            let authorization = try result.get()
            guard let credential = authorization.credential as? ASAuthorizationAppleIDCredential,
                  let identityToken = credential.identityToken,
                  let token = String(data: identityToken, encoding: .utf8) else {
                throw CloudAuthError.invalidAppleToken
            }
            guard let rawNonce = nonce else { throw CloudAuthError.invalidNonce }
            nonce = nil
            var request = URLRequest(url: CloudConfiguration.url.appendingPathComponent("auth/v1/token"))
            var components = URLComponents(url: request.url!, resolvingAgainstBaseURL: false)!
            components.queryItems = [URLQueryItem(name: "grant_type", value: "id_token")]
            request.url = components.url
            request.httpMethod = "POST"
            request.setValue(CloudConfiguration.publishableKey, forHTTPHeaderField: "apikey")
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONSerialization.data(withJSONObject: [
                "provider": "apple", "id_token": token, "nonce": rawNonce
            ])
            let (data, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse, (200...299).contains(http.statusCode) else {
                throw CloudAuthError.server
            }
            try saveSession(JSONDecoder().decode(CloudSession.self, from: data))
            error = nil
        } catch {
            self.error = error.localizedDescription
        }
    }

    func accessToken() async throws -> String {
        guard let current = session else { throw CloudAuthError.expired }
        if let expiresAt = current.expires_at, expiresAt > Int(Date().timeIntervalSince1970) + 90 {
            return current.access_token
        }
        var request = URLRequest(url: CloudConfiguration.url.appendingPathComponent("auth/v1/token"))
        var components = URLComponents(url: request.url!, resolvingAgainstBaseURL: false)!
        components.queryItems = [URLQueryItem(name: "grant_type", value: "refresh_token")]
        request.url = components.url
        request.httpMethod = "POST"
        request.setValue(CloudConfiguration.publishableKey, forHTTPHeaderField: "apikey")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: ["refresh_token": current.refresh_token])
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200...299).contains(http.statusCode),
              let renewed = try? JSONDecoder().decode(CloudSession.self, from: data),
              renewed.user.id == current.user.id else { throw CloudAuthError.expired }
        try saveSession(renewed)
        return renewed.access_token
    }

    func signOut() {
        session = nil
        userID = nil
        nonce = nil
        error = nil
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                    kSecAttrAccount as String: keychainAccount]
        SecItemDelete(query as CFDictionary)
    }

    private func saveSession(_ next: CloudSession) throws {
        let data = try JSONEncoder().encode(next)
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                    kSecAttrAccount as String: keychainAccount]
        SecItemDelete(query as CFDictionary)
        var attrs = query
        attrs[kSecValueData as String] = data
        attrs[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        guard SecItemAdd(attrs as CFDictionary, nil) == errSecSuccess else { throw CloudAuthError.server }
        session = next
        userID = next.user.id
    }

    private func readKeychain() -> Data? {
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                    kSecAttrAccount as String: keychainAccount,
                                    kSecReturnData as String: true,
                                    kSecMatchLimit as String: kSecMatchLimitOne]
        var result: CFTypeRef?
        guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess else { return nil }
        return result as? Data
    }
}
