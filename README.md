<<<<<<< HEAD
# Sensorbite
=======
Opis

Projekt prezentuje aplikacje do wyznaczania tras ewakuacji z uwzglednieniem zagrozen powodziowych. System laczy dane drogowe z OpenStreetMap z danymi satelitarnymi Sentinel Hub i wyznacza trase omijajaca zalane odcinki drog.

Aplikacja sklada sie z backendu w Python (FastAPI), ktory przetwarza dane przestrzenne i oblicza trase, oraz prostego interfejsu webowego umozliwiajacego wizualizacje mapy, flood zones i trasy ewakuacji. Calosc mozna uruchomic lokalnie jedna komenda przy uzyciu Dockera.


Proces uruchomienia i korzystania z aplikacji

1. Uruchomienie aplikacji

Aplikacja uruchamiana jest przy użyciu Docker Compose.

W katalogu głównym projektu należy wykonać polecenie:

docker compose up --build

Front odpali się na http://localhost:8080/

2. Pobranie danych drogowych 

Po wejściu na frontend użytkownik pracuje na mapie OpenStreetMap.

Pierwszym krokiem jest pobranie dróg dla aktualnego widoku mapy z możliwie ograniczonego obszaru:

użytkownik ustawia obszar na mapie,

kliknięcie przycisku "Pobierz drogi dla widoku" wysyła do backendu aktualny bounding box,

backend pobiera dane drogowe

dane są konwertowane do formatu GeoJSON,

na ich podstawie budowany jest graf dróg w pamięci aplikacji.

Po tym kroku graf dróg jest gotowy do dalszych obliczeń.

3. Nałożenie flood zones

Aplikacja obsługuje dwa sposoby pozyskania stref zalania.

Tryb Sentinel Hub:

kliknięcie przycisku "Pobierz strefy zalania dla widoku" powoduje pobranie obrazu satelitarnego przez Sentinel Hub OGC WMS,

obraz jest analizowany piksel po pikselu,

wykrywane są obszary zalania,

maska zalania jest konwertowana do poligonów,

poligony zapisywane są jako aktualne flood zones.

Tryb testowy:

użytkownik może uruchomić tryb testowy flood zones,

generowany jest sztuczny prostokątny obszar zalania,

tryb ten pozwala testować algorytm bez dostępu do Sentinel Hub.

4. Blokowanie zalanych odcinków dróg

Przed wyznaczeniem trasy backend:

wczytuje aktualne flood zones,

sprawdza przecinanie sie kazdej krawedzi grafu drog z poligonami zalania,

oznacza przecinajace sie odcinki jako zablokowane.

Zablokowane odcinki nie sa brane pod uwage przy wyznaczaniu trasy.

5. Wybor punktow START i META

Uzytkownik:

kliknieciem na mapie ustawia punkt START,

kliknieciem na mapie ustawia punkt META.

Punkty te sa automatycznie dopasowywane do najblizszych wezlow grafu drogowego.

6. Wyznaczenie trasy ewakuacji

Po kliknieciu przycisku "Wyznacz trase":

frontend wysyla zapytanie do endpointu:
GET /api/evac/route?start=lat,lon&end=lat,lon

backend buduje podgraf zawierajacy tylko niezablokowane odcinki,

uruchamiany jest algorytm najkrotszej sciezki,

wyznaczana jest trasa omijajaca zalane fragmenty,

wynik zwracany jest w formacie GeoJSON wraz z metadanymi.

7. Wizualizacja wyniku

Frontend:

rysuje trase ewakuacji na mapie,

wyswietla ja na tle drog i stref zalania,

pozwala latwo porownac trase z i bez zagrozen.

Podsumowanie procesu

Pelny proces dzialania aplikacji:

Uruchomienie aplikacji

Pobranie drog z OpenStreetMap

Pobranie lub wygenerowanie flood zones

Zablokowanie zalanych odcinkow

Ustawienie punktow START i META

Wyznaczenie trasy ewakuacji

Wizualizacja trasy na mapie





PLIKI

frontend/index.html
Interfejs uzytkownika oparty o HTML i JavaScript (Leaflet). Odpowiada za wyswietlanie mapy, interakcje uzytkownika oraz komunikacje z backendem.

Backend:

main.py
Punkt startowy aplikacji backendowej. Tworzy instancje FastAPI, konfiguruje middleware oraz rejestruje endpointy API.

routes.py
Definicja endpointow HTTP udostepnianych przez backend, w tym wyznaczania trasy oraz operacji administracyjnych.

evac_service.py
Glowna warstwa logiki aplikacji. Laczy pobieranie drog, przetwarzanie flood zones oraz wyznaczanie trasy ewakuacji.

osm_downloader.py
Pobiera dane drogowe z OpenStreetMap przy uzyciu Overpass API na podstawie bounding boxa.

osm_to_geojson.py
Konwertuje dane OSM w formacie XML do formatu GeoJSON.

graph_builder.py
Buduje graf drog (NetworkX) na podstawie danych GeoJSON.

sentinel_flood_ogc_client.py
Pobiera obrazy satelitarne z Sentinel Hub (OGC WMS) i przetwarza je na maske oraz poligony zalania.

flood_loader.py
Wczytuje flood zones zapisane w plikach GeoJSON do dalszego przetwarzania.

flood_intersector.py
Sprawdza przeciecia miedzy flood zones a odcinkami drog i oznacza zalane krawedzie jako zablokowane.

router.py
Odpowiada za wyznaczanie najkrotszej trasy ewakuacji z pominieciem zablokowanych odcinkow.

utils.py
Zawiera funkcje pomocnicze wykorzystywane w roznych modulach, miedzy innymi obliczanie odleglosci.



ENDPOINTY

Wyznaczanie trasy ewakuacji

GET /api/evac/route?start=lat,lon&end=lat,lon

Opis:
Wyznacza trase ewakuacji pomiedzy punktami START i META, z pominieciem zalanych odcinkow drog.

Parametry:

start: wspolrzedne punktu startowego (latitude, longitude)

end: wspolrzedne punktu docelowego (latitude, longitude)

Zwraca:

GeoJSON typu LineString reprezentujacy trase ewakuacji

metadane trasy (dlugosc, liczba segmentow, liczba zablokowanych odcinkow)

Operacje administracyjne (backend)

POST /api/admin/update-roads

Opis:
Pobiera dane drogowe z OpenStreetMap dla aktualnego obszaru mapy i przebudowuje graf drog.

Wejscie:

bounding box (south, west, north, east) w ciele zapytania

Zwraca:

komunikat statusowy potwierdzajacy pobranie i przetworzenie drog

POST /api/admin/update-flood

Opis:
Pobiera i przetwarza strefy zalania z Sentinel Hub dla aktualnego obszaru mapy.

Wejscie:

bounding box (south, west, north, east) w ciele zapytania

Zwraca:

komunikat statusowy potwierdzajacy aktualizacje flood zones

POST /api/admin/set-test-flood-rect

Opis:
Generuje testowy, sztuczny obszar zalania w postaci prostokata. Endpoint przeznaczony do testow i debugowania.

Wejscie:

bounding box (south, west, north, east) w ciele zapytania

Zwraca:

komunikat statusowy potwierdzajacy utworzenie testowych flood zones

Endpointy diagnostyczne

GET /api/debug/flood-geojson

Opis:
Zwraca aktualnie zaladowane strefy zalania w postaci GeoJSON.

Zwraca:

GeoJSON typu Polygon lub MultiPolygon reprezentujacy flood zones



Pomysly na rozwoj

Uwzglednienie danych czasowych (time series) z Sentinel Hub w celu sledzenia rozwoju zalania w czasie.

Dynamiczna aktualizacja flood zones w trakcie dzialania aplikacji.

Rozszerzenie algorytmu routingu o dodatkowe kryteria, takie jak typ drogi, predkosc ruchu lub przepustowosc.

Wprowadzenie wag dla krawedzi grafu w zaleznosci od poziomu zagrozenia.

Integracja z systemami i danymi meteorologicznymi.
>>>>>>> 433f28f (Działająca wersja)
