import SwiftUI

@main
struct MugeMugeApp: App {
    @StateObject private var workouts = WorkoutStore()
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
                .onAppear { _ = workouts.switchAccount(cloudAuth.userID) }
                .onChange(of: cloudAuth.userID) { _, userID in
                    _ = workouts.switchAccount(userID)
                }
        }
    }
}
