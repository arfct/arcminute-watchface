package com.artifact.chronology

import org.junit.Assert.assertEquals
import org.junit.Test

class DialMathTest {

    @Test
    fun hourAngle_threeThirty() {
        assertEquals(105f, DialMath.hourAngleDegrees(3, 30), 1e-4f)
    }

    @Test
    fun hourAngle_wrapsPm() {
        assertEquals(105f, DialMath.hourAngleDegrees(15, 30), 1e-4f)
    }

    @Test
    fun hourAngle_midnight() {
        assertEquals(0f, DialMath.hourAngleDegrees(0, 0), 1e-4f)
    }

    @Test
    fun unitVector_cardinalDirections() {
        // 12 o'clock: straight up (screen y grows down)
        assertEquals(0f, DialMath.unitX(0f), 1e-5f)
        assertEquals(-1f, DialMath.unitY(0f), 1e-5f)
        // 3 o'clock: to the right
        assertEquals(1f, DialMath.unitX(90f), 1e-5f)
        assertEquals(0f, DialMath.unitY(90f), 1e-5f)
    }

    @Test
    fun label12_zeroIsTwelve() {
        assertEquals(12, DialMath.label12(0))
        assertEquals(7, DialMath.label12(7))
    }

    @Test
    fun label24_afternoon() {
        // At 15:00 each tick shows the absolute hour nearest the current time:
        // the arc near the hand reads 13..17, ticks half a dial away read 21, 12.
        assertEquals(13, DialMath.label24(1, 15.0f))
        assertEquals(15, DialMath.label24(3, 15.0f))
        assertEquals(17, DialMath.label24(5, 15.0f))
        assertEquals(21, DialMath.label24(9, 15.0f))
        // Tick 0 is nearer to 12 than to 24 when it's 15:00
        assertEquals(12, DialMath.label24(0, 15.0f))
    }

    @Test
    fun label24_morning() {
        // At 09:00 the arc near the hand reads single-digit hours
        assertEquals(12, DialMath.label24(0, 9.0f))
        assertEquals(9, DialMath.label24(9, 9.0f))
        assertEquals(7, DialMath.label24(7, 9.0f))
        // Exactly 6h away ties round upward (matches the C truncation)
        assertEquals(15, DialMath.label24(3, 9.0f))
    }

    @Test
    fun label24_midnightWrap() {
        // Just after midnight the visible arc mixes ...23, 24, 1, 2...
        assertEquals(24, DialMath.label24(0, 0.5f))
        assertEquals(1, DialMath.label24(1, 0.5f))
        assertEquals(23, DialMath.label24(11, 0.5f))
    }

    @Test
    fun dialCenter_isOppositeHourDirection() {
        // At 12:00 (angle 0) unit=(0,-1): dial center sits BELOW screen center
        // by screenSize/2 + orbitInset.
        assertEquals(100f, DialMath.dialCenterX(100f, 0f, 200f, 180f), 1e-3f)
        assertEquals(100f + 280f, DialMath.dialCenterY(100f, 0f, 200f, 180f), 1e-3f)
        // At 3:00 (angle 90) unit=(1,0): dial center sits LEFT of screen center.
        assertEquals(100f - 280f, DialMath.dialCenterX(100f, 90f, 200f, 180f), 1e-3f)
        assertEquals(100f, DialMath.dialCenterY(100f, 90f, 200f, 180f), 1e-3f)
    }
}
