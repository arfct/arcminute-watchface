package com.artifact.chronology

import android.view.SurfaceHolder
import androidx.wear.watchface.ComplicationSlotsManager
import androidx.wear.watchface.Renderer
import androidx.wear.watchface.WatchFace
import androidx.wear.watchface.WatchFaceService
import androidx.wear.watchface.WatchFaceType
import androidx.wear.watchface.WatchState
import androidx.wear.watchface.style.CurrentUserStyleRepository
import androidx.wear.watchface.style.UserStyleSchema

class ChronologyWatchFaceService : WatchFaceService() {

    override fun createUserStyleSchema(): UserStyleSchema = StyleSchema.create(this)

    override suspend fun createWatchFace(
        surfaceHolder: SurfaceHolder,
        watchState: WatchState,
        complicationSlotsManager: ComplicationSlotsManager,
        currentUserStyleRepository: CurrentUserStyleRepository
    ): WatchFace {
        val renderer = ChronologyRenderer(
            applicationContext, surfaceHolder, currentUserStyleRepository, watchState
        )
        return WatchFace(WatchFaceType.ANALOG, renderer)
    }
}

class ChronologySharedAssets : Renderer.SharedAssets {
    override fun onDestroy() {}
}
