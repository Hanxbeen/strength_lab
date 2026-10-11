import Foundation

@main struct CatalogModelTests {
    static func main() throws {
        let metadataJSON = Data(#"{"schema_version":1,"items":[],"metadata":{"candidates":3,"requested":20,"awaiting_review":3,"checked_at":"2026-10-11T02:12:53Z"}}"#.utf8)
        let catalog = try JSONDecoder().decode(CatalogResponse.self, from: metadataJSON)
        assert(catalog.metadata?.candidates == 3)
        assert(catalog.metadata?.awaitingReview == 3)
        assert(catalog.items.isEmpty)
        assert(catalog.studies == nil)
        let studyJSON = Data(#"{"schema_version":1,"items":[],"studies":[{"pmid":"123","title":"Source","source_url":"https://pubmed.ncbi.nlm.nih.gov/123/","decision":"NOT_RUNNABLE","runnable":false,"reasons":[{"code":"MISSING_PRESCRIPTION","message":"Incomplete"}]}]}"#.utf8)
        let studyCatalog = try JSONDecoder().decode(CatalogResponse.self, from: studyJSON)
        assert(studyCatalog.studies?.count == 1)
        assert(studyCatalog.studies?.first?.isReadOnly == true)
        let forged = Data(String(decoding: studyJSON, as: UTF8.self).replacingOccurrences(of: "\"runnable\":false", with: "\"runnable\":true").utf8)
        let forgedCatalog = try JSONDecoder().decode(CatalogResponse.self, from: forged)
        assert(forgedCatalog.studies?.first?.isReadOnly == false)
        var json: [String: Any] = ["id":"test", "version":1,"title":"Test", "status":"PUBLISHED_PROTOCOL", "runnable":true, "description":"fixture", "sessions":[["id":"s","title":"S","exercises":[["id":"squat","name":"Squat","sets":3,"reps":5,"rest_seconds":180]]]], "source_type":"RESEARCH", "release_id":UUID().uuidString, "source_sha256":String(repeating:"a",count:64)]
        func decode(_ value: [String: Any]) throws -> TrainingProtocol {
            try JSONDecoder().decode(TrainingProtocol.self, from: JSONSerialization.data(withJSONObject:value))
        }
        let published = try decode(json)
        assert(published.isPublishedResearch)
        json["status"] = "REVOKED"
        let revoked = try decode(json)
        assert(!revoked.isPublishedResearch)
        json["status"] = "PUBLISHED_PROTOCOL"
        json.removeValue(forKey:"source_sha256")
        let missingSource = try decode(json)
        assert(!missingSource.isPublishedResearch)
        json["source_sha256"] = "invalid"
        let invalidSource = try decode(json)
        assert(!invalidSource.isPublishedResearch)
        print("CatalogModel: database metadata, published, revoked and missing-source checks passed")
    }
}
