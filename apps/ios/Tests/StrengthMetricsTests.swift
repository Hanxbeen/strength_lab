import Foundation

@main
struct StrengthMetricsTests {
    static func main() {
        assert(StrengthMetrics.estimatedOneRepMax(weightKg: 100, reps: 1) == 100)
        assert(abs(StrengthMetrics.estimatedOneRepMax(weightKg: 90, reps: 5)! - 105) < 0.00001)
        assert(StrengthMetrics.estimatedOneRepMax(weightKg: 90, reps: 11) == nil)
        assert(StrengthMetrics.estimatedOneRepMax(weightKg: -10, reps: 5) == nil)
        let logs = [
            LoggedSet(exerciseID: "squat", weightKg: 100, reps: 1),
            LoggedSet(exerciseID: "squat", weightKg: 90, reps: 5)
        ]
        assert(abs(StrengthMetrics.bestEstimatedOneRepMax(logs)! - 105) < 0.00001)
        assert(StrengthMetrics.volume(logs) == 550)
        print("StrengthMetrics: 6 assertions passed")
    }
}
