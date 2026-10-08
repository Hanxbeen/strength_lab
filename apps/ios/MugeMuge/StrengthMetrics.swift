import Foundation

enum StrengthMetrics {
    // Epley estimate. Display only as an estimate, not as a measured max.
    static func estimatedOneRepMax(weightKg: Double, reps: Int) -> Double? {
        guard weightKg > 0, weightKg.isFinite, (1...10).contains(reps) else { return nil }
        if reps == 1 { return weightKg }
        return weightKg * (1 + Double(reps) / 30)
    }

    static func bestEstimatedOneRepMax(_ sets: [LoggedSet]) -> Double? {
        sets.compactMap { estimatedOneRepMax(weightKg: $0.weightKg, reps: $0.reps) }.max()
    }

    static func volume(_ sets: [LoggedSet]) -> Double {
        sets.reduce(0) { $0 + $1.weightKg * Double($1.reps) }
    }
}
