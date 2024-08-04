package org.kivy;

import android.os.Bundle;
import android.os.ResultReceiver;
import android.media.session.MediaSession.Callback;
import android.content.Intent;
import java.lang.String;
import java.lang.System;
import android.view.KeyEvent;

import org.kivy.CallbackWrapper;

public class CustomMediaCallback extends Callback{

  public CallbackWrapper callback_wrapper;
  public CustomMediaCallback(CallbackWrapper callback_wrapper) {
    this.callback_wrapper = callback_wrapper;
  }
  @Override
  public boolean onMediaButtonEvent(Intent mediaButtonIntent) {
    KeyEvent ke = mediaButtonIntent.getParcelableExtra(Intent.EXTRA_KEY_EVENT);
    int keycode = ke.getKeyCode();
    this.callback_wrapper.button_pressed_keycode(keycode);
    return super.onMediaButtonEvent(mediaButtonIntent);
  }
  public void onPlay() {
    this.callback_wrapper.button_pressed("play");
  }
  public void onPause() {
    this.callback_wrapper.button_pressed("pause");
  }
  public void onStop() {
    this.callback_wrapper.button_pressed("stop");
  }
  public void onSkipToNext() {
    this.callback_wrapper.button_pressed("next");
  }
  public void onSkipToPrevious() {
    this.callback_wrapper.button_pressed("previous");
  }
  public void onFastForward() {
    this.callback_wrapper.button_pressed("forward");
  }
  public void onRewind() {
    this.callback_wrapper.button_pressed("backward");
  }
}
