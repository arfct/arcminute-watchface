package com.artifact.chronology

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import android.graphics.Typeface
import android.text.format.DateFormat
import android.view.SurfaceHolder
import androidx.core.content.res.ResourcesCompat
import androidx.wear.watchface.CanvasType
import androidx.wear.watchface.DrawMode
import androidx.wear.watchface.Renderer
import androidx.wear.watchface.WatchState
import androidx.wear.watchface.style.CurrentUserStyleRepository
import java.time.ZonedDateTime
import kotlin.math.abs
import kotlin.math.min

/**
 * Canvas port of the Pebble renderer (pebble/src/c/chronology.c).
 *
 * A dial three screen-heights wide is centered opposite the current hour
 * angle, so its rim (numerals + ticks) sweeps through the visible screen.
 * The hand runs from the dial center to the current-hour point on the rim.
 *
 * All pixel constants are gabbro (260 px) reference values scaled by
 * screenMinDim / 260.
 */
class ChronologyRenderer(
    private val context: Context,
    surfaceHolder: SurfaceHolder,
    private val styleRepository: CurrentUserStyleRepository,
    watchState: WatchState
) : Renderer.CanvasRenderer2<ChronologySharedAssets>(
    surfaceHolder,
    styleRepository,
    watchState,
    CanvasType.HARDWARE,
    interactiveDrawModeUpdateDelayMillis = 60_000L,
    clearWithBackgroundTintBeforeRenderingHighlightLayer = false
) {
    private val digitTypeface: Typeface =
        ResourcesCompat.getFont(context, R.font.helvetica_digits) ?: Typeface.DEFAULT

    private val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.FILL }
    private val strokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeCap = Paint.Cap.ROUND
    }
    private val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        typeface = digitTypeface
        textAlign = Paint.Align.LEFT
    }
    private val textBounds = Rect()

    override suspend fun createSharedAssets() = ChronologySharedAssets()

    override fun render(
        canvas: Canvas,
        bounds: Rect,
        zonedDateTime: ZonedDateTime,
        sharedAssets: ChronologySharedAssets
    ) {
        val ambient = renderParameters.drawMode == DrawMode.AMBIENT
        val style = if (ambient) {
            WatchStyle.fromUserStyle(styleRepository.userStyle.value).copy(
                bgColor = Color.BLACK,
                faceClear = true,
                handColor = Color.WHITE
            )
        } else {
            WatchStyle.fromUserStyle(styleRepository.userStyle.value)
        }

        val screenSize = min(bounds.width(), bounds.height()).toFloat()
        val scale = screenSize / 260f
        val cx = bounds.exactCenterX()
        val cy = bounds.exactCenterY()

        val hour = zonedDateTime.hour
        val minute = zonedDateTime.minute
        val angle = DialMath.hourAngleDegrees(hour, minute)

        // Dial geometry (update_frame_location)
        val orbitInset = 188f * scale
        val dialRadius = 1.5f * screenSize
        val dx = DialMath.dialCenterX(cx, angle, screenSize, orbitInset)
        val dy = DialMath.dialCenterY(cy, angle, screenSize, orbitInset)

        // Style-derived colors (face_color / face_text_color / face_minor_tick_color)
        val faceColor = if (style.faceClear) style.bgColor else style.faceColor
        val faceIsLight = colorIsLight(faceColor)
        val faceTextColor = if (faceIsLight) Color.BLACK else Color.WHITE
        val minorTickColor = if (faceIsLight) 0xFF555555.toInt() else 0xFFAAAAAA.toInt()

        // Dial style constants (gabbro reference pixels)
        val large = style.largeNumerals
        val hourInset = (if (large) 27.7f else 13.8f) * scale
        val hourTickStroke = strokeWidth(if (large) 6f else 3f, scale)
        // Same thickness as the hour ticks per user preference (Pebble used 4/2)
        val minorTickStroke = hourTickStroke
        // Dots match the minor tick width and end at the same outer radius
        val dotRadius = minorTickStroke / 2f
        // Pebble uses 9; thinned per user preference (kept in sync with the WFF flavor)
        val handStroke = strokeWidth(7f, scale)
        textPaint.textSize = (if (large) 95f else 42f) * scale
        textPaint.color = faceTextColor

        canvas.drawColor(style.bgColor)

        // Face disk, 8px (gabbro) beyond the marker ring
        if (!style.faceClear) {
            fillPaint.color = faceColor
            canvas.drawCircle(dx, dy, dialRadius + 8f * scale, fillPaint)
        }

        val use24h = DateFormat.is24HourFormat(context)
        val currentHour = hour + minute / 60f

        for (i in 0 until 12) {
            val tickAngle = i * 30f
            val ux = DialMath.unitX(tickAngle)
            val uy = DialMath.unitY(tickAngle)

            // Hour tick from (R - hourInset) to R; round caps extend half the
            // stroke past the endpoint, so pull the outer end in to land on R
            strokePaint.color = faceTextColor
            strokePaint.strokeWidth = hourTickStroke
            val hourOuter = dialRadius - hourTickStroke / 2f
            canvas.drawLine(
                dx + (dialRadius - hourInset) * ux, dy + (dialRadius - hourInset) * uy,
                dx + hourOuter * ux, dy + hourOuter * uy,
                strokePaint
            )

            // Numeral, placed inward from the tick so its nearest edge keeps a
            // gap of hourInset/2 along the radial direction
            val label = if (use24h) DialMath.label24(i, currentHour) else DialMath.label12(i)
            val text = label.toString()
            textPaint.getTextBounds(text, 0, text.length, textBounds)
            val halfW = textBounds.width() / 2f
            val halfH = textBounds.height() / 2f
            val tX = if (abs(ux) > 1e-6f) halfW / abs(ux) else Float.MAX_VALUE
            val tY = if (abs(uy) > 1e-6f) halfH / abs(uy) else Float.MAX_VALUE
            val dEdge = min(tX, tY)
            val gap = hourInset / 2f
            val innerRadius = dialRadius - hourInset
            val boxCenterX = dx + innerRadius * ux - (gap + dEdge) * ux
            val boxCenterY = dy + innerRadius * uy - (gap + dEdge) * uy
            canvas.drawText(
                text,
                boxCenterX - textBounds.exactCenterX(),
                boxCenterY - textBounds.exactCenterY(),
                textPaint
            )

            // Minor marks every 2.5 degrees: line ticks on 7.5-degree marks
            // (full-length at the half hour), dots elsewhere
            for (j in 1 until 12) {
                val minorAngle = tickAngle + j * 2.5f
                val mx = DialMath.unitX(minorAngle)
                val my = DialMath.unitY(minorAngle)
                if (j % 3 == 0) {
                    val tickInset = if (j == 6) hourInset else hourInset / 2f
                    strokePaint.color = minorTickColor
                    strokePaint.strokeWidth = minorTickStroke
                    val minorOuter = dialRadius - minorTickStroke / 2f
                    canvas.drawLine(
                        dx + (dialRadius - tickInset) * mx, dy + (dialRadius - tickInset) * my,
                        dx + minorOuter * mx, dy + minorOuter * my,
                        strokePaint
                    )
                } else {
                    fillPaint.color = minorTickColor
                    val dotCenter = dialRadius - dotRadius
                    canvas.drawCircle(dx + dotCenter * mx, dy + dotCenter * my, dotRadius, fillPaint)
                }
            }
        }

        // Hand: dial center to the current-hour point on the rim (my_hand_draw);
        // round cap pulled in so the tip ends on the same radius as the marks
        strokePaint.color = style.handColor
        strokePaint.strokeWidth = handStroke
        val handOuter = dialRadius - handStroke / 2f
        canvas.drawLine(
            dx, dy,
            dx + handOuter * DialMath.unitX(angle),
            dy + handOuter * DialMath.unitY(angle),
            strokePaint
        )
    }

    override fun renderHighlightLayer(
        canvas: Canvas,
        bounds: Rect,
        zonedDateTime: ZonedDateTime,
        sharedAssets: ChronologySharedAssets
    ) {
        canvas.drawColor(renderParameters.highlightLayer?.backgroundTint ?: Color.TRANSPARENT)
    }

    private fun strokeWidth(gabbroPx: Float, scale: Float): Float =
        (gabbroPx * scale).coerceAtLeast(1f)

    // Pebble color_is_light: 2-bit channel sum >= 5 of 9 -> 8-bit sum >= 425
    private fun colorIsLight(color: Int): Boolean =
        Color.red(color) + Color.green(color) + Color.blue(color) >= 425
}
