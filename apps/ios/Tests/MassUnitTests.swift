import Foundation

@main struct MassUnitTests {
    static func main() {
        let canonical = 100.0
        assert(abs(MassUnit.lb.display(canonical) - 220.46226218487757) < 1e-10)
        assert(abs(MassUnit.lb.kilograms(MassUnit.lb.display(canonical)) - canonical) < 1e-12)
        for unit in MassUnit.allCases {
            _ = unit.label(canonical)
            _ = unit.number(canonical)
        }
        assert(canonical == 100) // display functions have no write path
        assert(MassUnit.kg.parse("57,5") == 57.5)
        assert(MassUnit.kg.parse("") == nil)
        assert(MassUnit.kg.parse("-1") == nil)
        assert(MassUnit.kg.parse("NaN") == nil)
        assert(MassUnit.kg.parse("inf") == nil)
        assert(MassUnit.kg.parse("2001") == nil)
        assert(MassUnit.kg.parse("0") == nil)
        assert(MassUnit.kg.parse("0", allowsZero: true) == 0)
        assert(MassUnit.lb.parse("4500") == nil)
        assert(abs(MassUnit.lb.parse("220.5")! - 100.017117585) < 1e-9)
        assert(MassUnit.kg.input(100) == "100")
        assert(MassUnit.kg.input(0) == "0")
        assert(MassUnit.kg.input(57.5) == "57.5")
        assert(MassUnit.kg.step == 2.5 && MassUnit.lb.step == 5)
        print("MassUnit: conversion, bounds, display and direct input assertions passed")
    }
}
