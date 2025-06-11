# Drone-Car Synchronization Platform

Dataset i kod w projekcie umożliwia analizę danych z drona i pojazdu w celu synchronizacji czasowej i przestrzennej pomiędzy źródłami, przy wykorzystaniu znaczników ArUco. Główne zastosowanie to względna lokalizacja pojazdu na podstawie danych obrazowych i pozycyjnych.

![Widok z drona](test_platform/DJI_20250513140908_0373_D.JPG)

## Dane wejściowe

### 1. Zdjęcia drona
Pliki JPG zawierające obrazy wykonane z powietrza. W folderach `xx_loop` posortowane zdjęcia dotyczące konkretnych przejazdów przy konkretnej wysokości lotu i konkretnym ujęciu.

### 2. `drone_metadata.csv`
Zawiera informacje o lokalizacji drona w chwili wykonania każdego zdjęcia:
- `PhotoName`, `PhotoDate`, `PhotoTimestamp`
- `DroneLatitude`, `DroneLongitude`, `DroneAltitude`

### 3. `drone_car.csv`

Ten plik zawiera zsynchronizowane dane z drona i pojazdu, dopasowane na podstawie znaczników czasu (`PhotoTimestamp`). Każdy wiersz odpowiada jednej chwili wykonania zdjęcia przez drona i zawiera:

- `PhotoName`, `PhotoDate`, `PhotoTimestamp` – informacje o zdjęciu i czasie jego wykonania
- `DroneLatitude`, `DroneLongitude`, `DroneAltitude` – pozycja GPS drona
- `lat`, `lon`, `alt` – pozycja pojazdu w tym samym momencie (pochodząca z systemu lokalizacji auta)

Dzięki tym danym możliwe jest:
- wizualne porównanie położenia pojazdu na zdjęciach z danymi GPS,
- ocena dokładności synchronizacji,
- przeprowadzanie analiz lokalizacji względnej przy użyciu znaczników ArUco.

### 4. Pliki `.bag` (rosbag) w folderze rosbags
Zawierają dane z systemów pojazdu, np.:
- `/sensing/gnss/...`: pozycja i prędkość,
- `/localization/pose_twist_fusion_filter/kinematic_state`: estymowana pozycja,
- `/sensing/imu/imu_raw`: dane inercyjne.

Informacje o tematach i czasie dostępne są w `metadata.yaml`.


## Platforma testowa

### Dron DJI Mavic 3

### Platforma jezdna

![platform1](test_platform/DJI_20250513140934_0374_D.JPG)
![platform2](test_platform/DJI_20250513140936_0375_D.JPG)
![platform2](test_platform/DJI_20250513140938_0376_D.JPG)

## Wymagania
Python 3.8+

ROS 2 (do użycia rosbag)

biblioteki: `opencv-python`, `pandas`, `numpy`, `pyyaml`

## Autor

Autor: Piotr Zacholski
Operatorzy: Bartosz Ptak (dron), Stanisław Kuczma (platforma jezdna)
Data: czerwiec 2025

