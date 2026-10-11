import Foundation

/// Opt-in live smoke test; not included in offline test discovery.
@main struct LiveCatalog {
    @MainActor static func main() async {
        let catalog = CatalogStore()
        await catalog.refresh()
        precondition(catalog.error == nil, catalog.error ?? "")
        precondition(catalog.metadata != nil, "Expected a persisted batch summary")
        precondition(catalog.protocols.allSatisfy(\.isPublishedResearch))
        print("Live DB catalog: candidates=\(catalog.metadata!.candidates), awaiting=\(catalog.metadata!.awaitingReview), published=\(catalog.protocols.count)")
    }
}
