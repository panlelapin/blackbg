package app.blackbg

import android.app.Activity
import android.app.WallpaperManager
import android.graphics.Bitmap
import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.view.WindowInsets
import android.widget.Button
import android.widget.LinearLayout
import android.widget.Toast

class Preview : Activity() {
    companion object {
        init { System.loadLibrary("blackbg_arm64") }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val controls = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL
            setBackgroundColor(Color.BLACK)
            setOnApplyWindowInsetsListener { view, insets ->
                val bars = insets.getInsets(WindowInsets.Type.systemBars())
                view.setPadding(bars.left, bars.top, bars.right, bars.bottom)
                insets
            }
        }
        val apply = Button(this).apply { text = "Appliquer aux deux écrans" }
        val cancel = Button(this).apply {
            text = "Annuler"
            setOnClickListener { finish() }
        }
        apply.setOnClickListener {
            apply.isEnabled = false
            cancel.isEnabled = false
            Thread {
                val result = runCatching {
                    val black = Bitmap.createBitmap(1, 1, Bitmap.Config.ARGB_8888)
                    black.eraseColor(Color.BLACK)
                    val manager = WallpaperManager.getInstance(this)
                    check(manager.isWallpaperSupported && manager.isSetWallpaperAllowed)
                    check(manager.setBitmap(black, null, false,
                        WallpaperManager.FLAG_SYSTEM or WallpaperManager.FLAG_LOCK) > 0)
                }
                runOnUiThread {
                    if (!isDestroyed && !isFinishing) {
                        if (result.isSuccess) {
                            setResult(RESULT_OK)
                            finish()
                        } else {
                            Toast.makeText(this, "Impossible d’appliquer le fond noir.", Toast.LENGTH_LONG).show()
                            apply.isEnabled = true
                            cancel.isEnabled = true
                        }
                    }
                }
            }.start()
        }
        controls.addView(apply)
        controls.addView(cancel)
        setContentView(controls)
    }
}
