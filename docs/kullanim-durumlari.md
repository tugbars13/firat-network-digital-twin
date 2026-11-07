@startuml
left to right direction
skinparam actorStyle awesome
skinparam packageStyle rectangle
skinparam shadowing false
skinparam defaultFontName Arial

title Kampüs Ağı Dijital İkizi — Use Case Diyagramı

actor "Teknik personel" as Tek
actor "Ağ yöneticisi" as Yon
actor "Telemetri simülatörü" as Sim <<sistem>>

Yon -|> Tek

rectangle "Kampüs Ağı Dijital İkizi" {
  usecase "UC-01\nKampüs ağını\n3D görüntüle" as UC01
  usecase "UC-02\nCanlı telemetriyi izle" as UC02
  usecase "UC-03\nCihaz detayını incele" as UC03
  usecase "UC-04\nHat detayını incele" as UC04
  usecase "UC-05\nUyarıları görüntüle" as UC05
  usecase "UC-06\nUyarıyı onayla" as UC06
  usecase "UC-07\nGeçmişi tekrar oynat" as UC07
  usecase "UC-08\nArıza senaryosu çalıştır" as UC08
  usecase "UC-09\nKapasite senaryosu çalıştır" as UC09
  usecase "UC-10\nTopolojiyi içe aktar" as UC10
  usecase "UC-11\nTelemetri gönder" as UC11
}

Tek -- UC01
Tek -- UC02
Tek -- UC03
Tek -- UC04
Tek -- UC05
Tek -- UC06

Yon -- UC07
Yon -- UC08
Yon -- UC09
Yon -- UC10

UC11 -- Sim
@enduml