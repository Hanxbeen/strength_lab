import SwiftUI

@main
struct MugeMugeApp: App {
    @StateObject private var workouts = WorkoutStore()
    @StateObject private var catalog = CatalogStore()
    @StateObject private var cloudAuth = CloudAuth()

    var body: some Scene {
        WindowGroup {
            HomeView()
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
