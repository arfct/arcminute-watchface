package com.artifact.chronology

import android.graphics.Color
import androidx.wear.watchface.style.UserStyle
import androidx.wear.watchface.style.UserStyleSetting

/** Resolved style values used by the renderer. Defaults match the Pebble defaults. */
data class WatchStyle(
    val bgColor: Int = Color.BLACK,
    val faceColor: Int = Color.BLACK,
    val handColor: Int = COLOR_RED,
    val faceClear: Boolean = true,
    val largeNumerals: Boolean = true
) {
    companion object {
        // Tailwind red-500
        const val COLOR_RED = 0xFFEF4444.toInt()

        // Tailwind CSS 500-series palette (kept in sync with the WFF flavor's
        // generate_watchface.py)
        val TAILWIND: List<Pair<String, Int>> = listOf(
            "red" to COLOR_RED,
            "orange" to 0xFFF97316.toInt(),
            "amber" to 0xFFF59E0B.toInt(),
            "yellow" to 0xFFEAB308.toInt(),
            "lime" to 0xFF84CC16.toInt(),
            "green" to 0xFF22C55E.toInt(),
            "emerald" to 0xFF10B981.toInt(),
            "teal" to 0xFF14B8A6.toInt(),
            "cyan" to 0xFF06B6D4.toInt(),
            "sky" to 0xFF0EA5E9.toInt(),
            "blue" to 0xFF3B82F6.toInt(),
            "indigo" to 0xFF6366F1.toInt(),
            "violet" to 0xFF8B5CF6.toInt(),
            "purple" to 0xFFA855F7.toInt(),
            "fuchsia" to 0xFFD946EF.toInt(),
            "pink" to 0xFFEC4899.toInt(),
            "rose" to 0xFFF43F5E.toInt()
        )

        private val COLORS: Map<String, Int> = buildMap {
            put("black", Color.BLACK)
            put("white", Color.WHITE)
            put("gray", 0xFFAAAAAA.toInt())
            putAll(TAILWIND)
        }

        fun fromUserStyle(userStyle: UserStyle): WatchStyle {
            var style = WatchStyle()
            for ((setting, option) in userStyle) {
                val optionId = String(option.id.value)
                when (setting.id.value) {
                    StyleSchema.ID_DIAL_STYLE ->
                        style = style.copy(largeNumerals = optionId == StyleSchema.OPTION_LARGE)
                    StyleSchema.ID_BG_COLOR ->
                        style = style.copy(bgColor = COLORS[optionId] ?: Color.BLACK)
                    StyleSchema.ID_FACE_COLOR ->
                        style = style.copy(faceColor = COLORS[optionId] ?: Color.BLACK)
                    StyleSchema.ID_HAND_COLOR ->
                        style = style.copy(handColor = COLORS[optionId] ?: COLOR_RED)
                    StyleSchema.ID_FACE_CLEAR -> {
                        val on = (option as? UserStyleSetting.BooleanUserStyleSetting.BooleanOption)
                            ?.value ?: true
                        style = style.copy(faceClear = on)
                    }
                }
            }
            return style
        }
    }
}
