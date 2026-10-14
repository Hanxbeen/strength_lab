import SwiftUI

@main
struct MugeMugeApp: App {
    @StateObject private var workouts: WorkoutStore = {
        #if DEBUG
        if let name = ProcessInfo.processInfo.environment["MUGEMUGE_UI_TEST_FILE"],
           name.hasPrefix("ui-test-"), !name.contains("/") {
            return WorkoutStore(filename: name)
        }
        #endif
        return WorkoutStore()
    }()
    @StateObject private var catalog = CatalogStore()
    @StateObject private var cloudAuth = CloudAuth()

    var body: some Scene {
        WindowGroup {
            ApprovedHomeView()
                .id(cloudAuth.userID)
                .environment(\.locale, Locale(identifier: "ko_KR"))
                .environmentObject(workouts)
                .environmentObject(catalog)
                .environmentObject(cloudAuth)
                .onAppear {
                    #if DEBUG
                    if ProcessInfo.processInfo.environment["MUGEMUGE_UI_TEST_FILE"] != nil { return }
                    #endif
                    _ = workouts.switchAccount(cloudAuth.userID)
                }
                .onChange(of: cloudAuth.userID) { _, userID in
                    #if DEBUG
                    if ProcessInfo.processInfo.environment["MUGEMUGE_UI_TEST_FILE"] != nil { return }
                    #endif
                    _ = workouts.switchAccount(userID)
                }
        }
    }
}
