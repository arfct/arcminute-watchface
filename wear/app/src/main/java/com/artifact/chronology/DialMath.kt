package com.artifact.chronology

import kotlin.math.cos
import kotlin.math.sin

/**
 * Pure geometry for the orbiting dial, ported from pebble/src/c/chronology.c.
 *
 * Angles are clock angles: degrees clockwise from 12 o'clock. Screen
 * coordinates have y growing downward, so the unit vector for a clock angle
 * is (sin, -cos).
 */
object DialMath {

    /** Hour-hand angle: 30 degrees per hour plus minute fraction. */
    fun hourAngleDegrees(hour: Int, minute: Int): Float =
        30f * ((hour % 12) + minute / 60f)

    fun unitX(angleDeg: Float): Float = sin(Math.toRadians(angleDeg.toDouble())).toFloat()

    fun unitY(angleDeg: Float): Float = (-cos(Math.toRadians(angleDeg.toDouble()))).toFloat()

    /**
     * Dial center sits opposite the hour direction, at screenSize/2 + orbitInset
     * from the screen center (Pebble's update_frame_location).
     */
    fun dialCenterX(cx: Float, angleDeg: Float, screenSize: Float, orbitInset: Float): Float =
        cx - (screenSize / 2f + orbitInset) * unitX(angleDeg)

    fun dialCenterY(cy: Float, angleDeg: Float, screenSize: Float, orbitInset: Float): Float =
        cy - (screenSize / 2f + orbitInset) * unitY(angleDeg)

    /** 12h dial label for tick [index] (0..11): 0 -> 12, else the index. */
    fun label12(index: Int): Int = if (index == 0) 12 else index

    /**
     * 24h dial label for tick [index]: the absolute hour (1-24) nearest the
     * current time, so the visible arc reads 13-24 in the afternoon and mixes
     * across midnight (...23, 24, 1, 2...) as the dial rolls over.
     */
    fun label24(index: Int, currentHour: Float): Int {
        val laps = (currentHour - index) / 12.0f
        val nearest = index + 12 * (laps + if (laps >= 0) 0.5f else -0.5f).toInt()
        val wrapped = ((nearest % 24) + 24) % 24
        return if (wrapped == 0) 24 else wrapped
    }
}
