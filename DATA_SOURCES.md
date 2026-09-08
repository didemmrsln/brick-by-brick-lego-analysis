# Veri Kaynağı Seçim Metodolojisi

Bu proje Rebrickable'ın açık veri setini temel alıyor, ancak Rebrickable'ın
resmi API dokümantasyonunda da açıkça belirtildiği gibi bu veri setinde hiçbir
fiyat bilgisi bulunmuyor — ne orijinal satış fiyatı (retail/MSRP), ne de
ikincil piyasa değeri. Bölüm 2 (parça sayısı, tema ve yıldan fiyat tahmini)
ve Faz 3 (retired sonrası bir setin değerinin nasıl arttığı) doğrudan fiyat
verisine bağlı olduğu için, Rebrickable'a ek/tamamlayıcı dört farklı harici
kaynak araştırıldı ve her biri gerçek veriyle test edildi.

## İncelenen kaynaklar

**Brickset**, LEGO setleri için ücretsiz ve canlı bir API sunuyor; `getSets`
metodu üzerinden LEGO'nun kendi online mağazasında (lego.com) uygulanan
perakende (retail/MSRP) fiyatını döndürüyor. Günlük 100 çağrı sınırı yeterince
yüksek olduğu için, `sets_clean.csv`'deki analiz-hazır 75 farklı yılın (1949–
2025) tamamı tek bir oturumda, yıl bazlı sorgularla toplu olarak çekildi ve
kesintiye dayanıklı (resumable) bir önbellekleme mekanizmasıyla kaydedildi.
Sonuç olarak 18.190 analiz-hazır setin 6.614'ü (%36.4) retail fiyatıyla
eşleşti. Ancak bu eşleşen alt küme rastgele bir örneklem değil: medyan yılı
2017 iken eşleşmeyenlerin medyan yılı 2003; medyan parça sayısı 224 iken
eşleşmeyenlerinki sadece 35. Bunun nedeni basit — Brickset'in
`retailPrice` alanı yalnızca LEGO'nun kendi online mağazasında satılmış
setler için doluyor, ve bu mağaza esas olarak 2000'lerin ortasından
itibaren önem kazanmış, öncelikli olarak ana ürün hattındaki (flagship)
setleri kapsamış; küçük parça paketleri, servis parçaları ve eski/yardımcı
kategoriler bu kanaldan hiç satılmadığı için sistematik olarak dışarıda
kalıyor.

**BrickEconomy** en zengin veri setini sunuyor — retail fiyatın yanı sıra
güncel piyasa değeri (`current_value_new`/`used`), yıllık büyüme oranı
(`rolling_growth`) ve 2-5 yıllık fiyat tahmini (`forecast_value`) gibi
Brickset'te veya başka hiçbir kaynakta bulunmayan alanları içeriyor. Ancak bu
zenginliğin bedeli var: API'ye erişim aylık ücretli bir Premium abonelik
(~250 TL/ay) gerektiriyor ve — Premium hesapta bile — günde 100, dakikada 4
istekle sınırlı. Bu limit, Brickset'te uygulanan "tüm popülasyonu tek
oturumda tara" stratejisini burada imkansız kılıyor; bunun yerine öncelik
sırasına dayalı, aylara yayılan bir örneklem stratejisi benimsenmesi
gerekiyor.

**GitHub üzerindeki `rpmoo/lego-eda` projesi**, BrickLink'in Price Guide
API'sinden çekilmiş gerçek new/used piyasa fiyatı verisi içeriyor ve
`set_num` formatı bizimkiyle birebir uyumlu — 15.497 satırlık bu veri
setinin 13.197'si bizim setlerimizle eşleşiyor. Ne var ki veri, commit
geçmişinden anlaşıldığı kadarıyla Ekim 2020'de tek seferlik çekilmiş ve o
tarihten beri güncellenmemiş, donmuş bir anlık görüntü; ayrıca kaynak kodu
incelendiğinde, API çağrısı başarısız olduğunda ("hata") ile setin
gerçekten hiç piyasa kaydının olmaması durumunun ("gerçek sıfır") kodda
aynı `except` bloğunda ayırt edilmeden ikisinin de 0 değerine düştüğü
görüldü — bu da sıfır değerlerin güvenilirliğini zayıflatıyor. Bu nedenle
bu kaynak ana veri kaynağı olarak kullanılmıyor; hem verinin yaşı hem de
projenin kendi altyapısının (Brickset + BrickEconomy) zaten daha geniş ve
güncel bir kapsam sunması bu kararı destekliyor.

**Kaggle üzerindeki `alexracape/lego-sets-and-prices-over-time`** veri seti
de incelendi; Mayıs 2023 tarihli olduğu belirtiliyor. Ancak şemasına
bakıldığında (`Theme_Group`, `Subtheme`, `Availability` gibi alan adları)
Brickset'in kendi API alan isimleriyle neredeyse birebir örtüştüğü fark
edildi — yani bu, bağımsız bir üçüncü kaynak değil, büyük olasılıkla
Brickset verisinin belirli bir tarihte alınmış donmuş bir kopyası. Bu
nedenle ana kaynak olarak kullanılmıyor; ancak ileride Brickset'in kendi
canlı verisiyle çapraz doğrulama yapılması gerekirse referans olarak
saklanıyor.

Son olarak **BrickLink'in kendi API'sine doğrudan erişim** denendi, ancak
BrickLink'in Marketplace hizmeti Türkiye'de sunulmadığı için "Seller Only
Area" / alıcı-satıcı yeteneklerinin kullanılamadığına dair bir hata alındı.
Bu kaynak kapsam dışı bırakıldı.

## Nihai karar

Bölüm 2'deki temel fiyat tahmini regresyonu **Brickset verisiyle, mevcut
haliyle (n=6.614)** yapılacak. Ancak bu örneklemin rastgele bir kesit
olmadığı — modelin kapsamının aslında "2015 sonrası, lego.com kanalıyla
satılmış, çoğunlukla flagship/büyük setler" popülasyonuyla sınırlı olduğu
— raporda açık bir limitasyon olarak belirtilecek, örtük biçimde genel
popülasyonu temsil ediyormuş gibi sunulmayacak. Faz 3'teki retired-sonrası
değer artışı analizi için ise **BrickEconomy ana kaynak** olacak, çünkü
`current_value`, `growth` ve `forecast` alanları yalnızca orada mevcut.
`rpmoo/lego-eda` ve Kaggle kaynakları aktif kullanılmayacak; ikisi de
ilerideki bir çapraz-doğrulama ihtiyacı için `data/external/` altında
referans olarak tutulacak.
