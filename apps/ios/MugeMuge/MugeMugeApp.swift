import SwiftUI

@main
struct MugeMugeApp: App {
    @StateObject private var workouts = WorkoutStore()
    @StateObject private var catalog = CatalogStore()
    @StateObject private var training = TrainingState()

    var body: some Scene {
        WindowGroup {
            HomeView()
                .environmentObject(workouts)
                .environmentObject(catalog)
                .environmentObject(training)
        }
    }
}
