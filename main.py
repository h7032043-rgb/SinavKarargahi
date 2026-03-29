import datetime
import random
import json
import os
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from plyer import notification

Window.size = (360, 640)

# --- TASARIM KODU (KV) ---
KV = '''
MDScreenManager:
    GirisEkrani:
    AnaEkran:
    AyarlarEkrani:

<GirisEkrani>:
    name: "giris"
    MDFloatLayout:
        md_bg_color: 0.1, 0.1, 0.2, 1
        MDLabel:
            text: "SINAV TAKİP SİSTEMİ"
            halign: "center"
            pos_hint: {"center_y": .75}
            font_style: "H4"
            theme_text_color: "Custom"
            text_color: 0.2, 0.7, 1, 1
            bold: True
        MDTextField:
            id: isim_field
            hint_text: "Adınız nedir?"
            pos_hint: {"center_x": .5, "center_y": .5}
            size_hint_x: .7
            mode: "round"
        MDRaisedButton:
            text: "BAŞLAYALIM"
            pos_hint: {"center_x": .5, "center_y": .4}
            size_hint_x: .7
            on_release: app.isim_kaydet(isim_field.text)

<AnaEkran>:
    name: "ana"
    MDFloatLayout:
        md_bg_color: 0.05, 0.05, 0.1, 1
        
        MDTopAppBar:
            title: "Sınavlarım"
            anchor_title: "left"
            pos_hint: {"top": 1}
            elevation: 4
            md_bg_color: 0.1, 0.1, 0.2, 1
            left_action_items: [["cog", lambda x: app.ekran_degistir("ayarlar")]]

        MDLabel:
            id: hosgeldin_label
            text: ""
            pos_hint: {"x": .05, "top": .88}
            size_hint_y: None
            height: "40dp"
            font_style: "H6"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1

        ScrollView:
            pos_hint: {"top": .82}
            size_hint_y: .75
            MDBoxLayout:
                id: sinav_listesi
                orientation: "vertical"
                adaptive_height: True
                padding: "20dp"
                spacing: "20dp"

        MDFloatingActionButton:
            icon: "plus"
            pos_hint: {"center_x": .85, "center_y": .08}
            md_bg_color: 0.2, 0.6, 1, 1
            on_release: app.ekleme_diyalog_ac()

<AyarlarEkrani>:
    name: "ayarlar"
    MDBoxLayout:
        orientation: "vertical"
        padding: "20dp"
        spacing: "20dp"
        md_bg_color: 0.05, 0.05, 0.1, 1
        
        MDLabel:
            text: "AYARLAR"
            font_style: "H4"
            halign: "center"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            
        MDTextField:
            id: ayar_isim
            hint_text: "İsmi Değiştir"
            mode: "rectangle"
            
        MDRaisedButton:
            text: "İSMİ GÜNCELLE"
            size_hint_x: 1
            on_release: app.isim_guncelle(ayar_isim.text)
            
        MDRaisedButton:
            text: "ANA EKRANA DÖN"
            size_hint_x: 1
            md_bg_color: 0.3, 0.3, 0.3, 1
            on_release: app.ekran_degistir("ana")
'''

class GirisEkrani(MDScreen): pass
class AnaEkran(MDScreen): pass
class AyarlarEkrani(MDScreen): pass

class SinavTakipApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.sinavlar = []
        self.kullanici_adi = ""
        self.dosya_yolu = "karargah_v9.json"
        self.verileri_yukle()
        
        return Builder.load_string(KV)

    def on_start(self):
        if self.kullanici_adi:
            self.root.current = "ana"
            self.ana_ekran_guncelle()
        # Her saniye listeyi güncellemek için saat ekle
        Clock.schedule_interval(self.liste_tazele, 1)

    def isim_kaydet(self, isim):
        if isim:
            self.kullanici_adi = isim
            self.verileri_kaydet()
            self.root.current = "ana"
            self.ana_ekran_guncelle()

    def isim_guncelle(self, yeni_isim):
        if yeni_isim:
            self.kullanici_adi = yeni_isim
            self.verileri_kaydet()
            self.ana_ekran_guncelle()

    def ekran_degistir(self, ekran_adi):
        self.root.current = ekran_adi

    def ana_ekran_guncelle(self):
        ana = self.root.get_screen("ana")
        ana.ids.hosgeldin_label.text = f"Hoş geldin, {self.kullanici_adi}!"
        self.liste_tazele()

    def ekleme_diyalog_ac(self):
        icerik = MDBoxLayout(orientation="vertical", spacing="5dp", size_hint_y=None, height="320dp")
        self.ad_in = TextInput(hint_text="Sınav Adı (örn: Mat)", multiline=False)
        self.gun_in = TextInput(hint_text="Gün", input_filter="int")
        self.ay_in = TextInput(hint_text="Ay", input_filter="int")
        self.saat_in = TextInput(hint_text="Saat", input_filter="int")
        self.dak_in = TextInput(hint_text="Dakika", input_filter="int")
        self.periyot_in = TextInput(hint_text="Bildirim Aralığı (Dakika)", input_filter="int")
        
        for i in [self.ad_in, self.gun_in, self.ay_in, self.saat_in, self.dak_in, self.periyot_in]:
            icerik.add_widget(i)

        self.diyalog = MDDialog(
            title="Sınav Detayları",
            type="custom",
            content_cls=icerik,
            buttons=[
                MDRaisedButton(text="KAYDET", on_release=self.sinav_ekle),
            ],
        )
        self.diyalog.open()

    def sinav_ekle(self, *args):
        try:
            hedef_zaman = datetime.datetime(2026, int(self.ay_in.text), int(self.gun_in.text), 
                                          int(self.saat_in.text), int(self.dak_in.text))
            yeni = {
                "id": str(random.randint(1000, 9999)),
                "ad": self.ad_in.text,
                "vakit": hedef_zaman.strftime("%Y-%m-%d %H:%M"),
                "eklenme": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "periyot": int(self.periyot_in.text),
                "son_bildirim": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            self.sinavlar.append(yeni)
            self.verileri_kaydet()
            self.diyalog.dismiss()
        except: pass

    def liste_tazele(self, *args):
        if self.root.current != "ana": return
        
        liste = self.root.get_screen("ana").ids.sinav_listesi
        liste.clear_widgets()
        
        for s in self.sinavlar:
            vakit = datetime.datetime.strptime(s['vakit'], "%Y-%m-%d %H:%M")
            eklenme = datetime.datetime.strptime(s['eklenme'], "%Y-%m-%d %H:%M")
            simdi = datetime.datetime.now()
            
            kalan = vakit - simdi
            toplam_vakit = (vakit - eklenme).total_seconds()
            gecen_vakit = (simdi - eklenme).total_seconds()
            
            # Progress Bar Hesaplama
            oran = min(100, max(0, (gecen_vakit / toplam_vakit) * 100)) if toplam_vakit > 0 else 100
            
            if kalan.total_seconds() > 0:
                zaman_metni = f"{kalan.days}g {kalan.seconds//3600}s {(kalan.seconds//60)%60}d {kalan.seconds%60}sn"
            else:
                zaman_metni = "Sınav Başladı!"

            kart = MDCard(orientation="vertical", padding="15dp", size_hint=(1, None), height="140dp", 
                          radius=[20,], md_bg_color=(0.1, 0.15, 0.3, 1), elevation=3)
            
            kart.add_widget(Label(text=s['ad'].upper(), bold=True, font_size="18sp", color=(0.4, 0.8, 1, 1)))
            kart.add_widget(Label(text=zaman_metni, font_size="14sp"))
            
            # Dolan Bar
            pb = ProgressBar(max=100, value=oran, size_hint_y=None, height="20dp")
            kart.add_widget(pb)
            
            btn_sil = MDIconButton(icon="trash-can", pos_hint={"right": 1}, theme_text_color="Custom", text_color=(1,0.2,0.2,1))
            btn_sil.bind(on_release=lambda x, sid=s['id']: self.sinav_sil(sid))
            kart.add_widget(btn_sil)
            
            liste.add_widget(kart)
            self.bildirim_kontrol(s)

    def sinav_sil(self, sid):
        self.sinavlar = [s for s in self.sinavlar if s['id'] != sid]
        self.verileri_kaydet()

    def bildirim_kontrol(self, s):
        simdi = datetime.datetime.now()
        son = datetime.datetime.strptime(s['son_bildirim'], "%Y-%m-%d %H:%M")
        if (simdi - son).total_seconds() / 60 >= s['periyot']:
            notification.notify(title=f"Sınav Hatırlatıcı: {s['ad']}", message="Zaman geçiyor, çalışmaya devam!")
            s['son_bildirim'] = simdi.strftime("%Y-%m-%d %H:%M")
            self.verileri_kaydet()

    def verileri_kaydet(self):
        with open(self.dosya_yolu, "w") as f:
            json.dump({"isim": self.kullanici_adi, "sinavlar": self.sinavlar}, f)

    def verileri_yukle(self):
        if os.path.exists(self.dosya_yolu):
            try:
                with open(self.dosya_yolu, "r") as f:
                    data = json.load(f)
                    self.kullanici_adi = data.get("isim", "")
                    self.sinavlar = data.get("sinavlar", [])
            except: pass

if __name__ == "__main__":
    SinavTakipApp().run()