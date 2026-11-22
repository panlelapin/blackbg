package audit.check;
import android.app.*;
import android.app.admin.*;
import android.content.*;
import android.os.*;
import android.util.Log;
public class Probe extends Activity {
  public static class Admin extends DeviceAdminReceiver {}
  protected void onCreate(Bundle state) {
    super.onCreate(state);
    if (state != null) return;
    String mode = getIntent().getStringExtra("mode");
    if (mode == null) {
      startActivityForResult(new Intent(Intent.ACTION_SET_WALLPAPER).setPackage("com.github.panlelapin.blackbg"), 1);
    } else {
      DevicePolicyManager d = getSystemService(DevicePolicyManager.class);
      ComponentName admin = new ComponentName(this, Admin.class);
      if (mode.equals("deny")) d.addUserRestriction(admin, UserManager.DISALLOW_SET_WALLPAPER);
      else d.clearUserRestriction(admin, UserManager.DISALLOW_SET_WALLPAPER);
      finish();
    }
  }
  protected void onActivityResult(int req, int result, Intent data) {
    super.onActivityResult(req, result, data);
    Log.i("WallAuditResult","result="+result);
    finish();
  }
}
