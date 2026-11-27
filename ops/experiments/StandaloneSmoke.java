import javax.swing.JFrame;
import javax.swing.SwingUtilities;
import java.awt.Frame;

/** Optional graphical startup check using only the assembled application's class path. */
public class StandaloneSmoke {
  public static void main(String[] args) throws Exception {
    SwingUtilities.invokeAndWait(() -> {
      org.swrltab.ui.SWRLTab.main(args);
      org.swrltab.ui.SQWRLTab.main(args);
      int windows = 0;
      for (Frame frame : Frame.getFrames()) {
        if (frame instanceof org.swrltab.ui.SWRLTab || frame instanceof org.swrltab.ui.SQWRLTab) {
          if (!frame.isShowing() || ((JFrame)frame).getContentPane().getComponentCount() == 0)
            throw new AssertionError("Standalone view did not become visible");
          windows++;
        }
      }
      if (windows != 2) throw new AssertionError("Expected both standalone application windows, got " + windows);
      System.out.println("PASS: packaged SWRLTab and SQWRLTab entry points display their graphical views");
      for (Frame frame : Frame.getFrames()) frame.dispose();
    });
  }
}
