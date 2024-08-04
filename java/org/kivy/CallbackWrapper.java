package org.kivy;
import java.lang.String;

public interface CallbackWrapper {
  public void button_pressed(String button);
  public void button_pressed_keycode(int keycode);
}
