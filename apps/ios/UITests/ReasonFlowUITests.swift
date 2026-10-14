import XCTest

final class ReasonFlowUITests: XCTestCase {
    func reveal(_ element: XCUIElement, in app: XCUIApplication) {
        for _ in 0..<6 {
            if element.isHittable { return }
            app.swipeUp()
        }
        XCTAssertTrue(element.isHittable)
    }
    func testChangeReasonAndRestore() {
        continueAfterFailure = false
        let app = XCUIApplication()
        app.launchEnvironment["MUGEMUGE_UI_TEST_FILE"] = "ui-test-" + UUID().uuidString + ".json"
        app.launchArguments = ["-onboardingCompleted.v2", "YES", "-homeHelpDismissed.v2", "YES"]
        app.launch()
        let entry = app.staticTexts["운동이 처음이라면"]
        XCTAssertTrue(entry.waitForExistence(timeout: 15))
        reveal(entry, in: app)
        entry.tap()
        let start = app.buttons["시작 무게 확인"]
        XCTAssertTrue(start.waitForExistence(timeout: 5))
        reveal(start, in: app)
        start.tap()
        for index in 0..<3 {
            let field = app.textFields.element(boundBy: index)
            reveal(field, in: app)
            field.tap()
            field.typeText("80")
        }
        let begin = app.buttons["이 중량으로 운동 시작"]
        reveal(begin, in: app)
        begin.tap()
        let weight = app.textFields["이번 세트 중량, kg"]
        XCTAssertTrue(weight.waitForExistence(timeout: 5))
        weight.tap()
        weight.typeText(String(repeating: XCUIKeyboardKey.delete.rawValue, count: 12) + "75")
        let apply = app.buttons["이번 세트 중량 적용"]
        reveal(apply, in: app)
        apply.tap()
        XCTAssertTrue(app.buttons["힘이 부족했어요"].waitForExistence(timeout: 5))
        app.buttons["힘이 부족했어요"].tap()
        app.buttons["통증·불편함"].tap()
        app.buttons["사유 저장"].tap()
        let paused = app.staticTexts["통증·불편함을 기록해 일시정지했어요."]
        XCTAssertTrue(paused.waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["세트 완료"].isEnabled)
        app.terminate()
        app.launch()
        let resume = app.buttons["운동 이어하기"]
        XCTAssertTrue(resume.waitForExistence(timeout: 10))
        resume.tap()
        XCTAssertTrue(paused.waitForExistence(timeout: 5))
        app.buttons["기록을 남기고 종료"].firstMatch.tap()
        let skip = app.buttons["건너뛰기"]
        if skip.waitForExistence(timeout: 3) { skip.tap() }
        XCTAssertTrue(app.buttons["운동 화면 닫기"].waitForExistence(timeout: 5))
    }
}
