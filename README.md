# LLM Systems Playground — Python → C++ Benchmark

## Nedir?
Bu repo, farklı LLM’lerin Python kodunu C++’a çevirme performansını karşılaştırmak için oluşturuldu. Çalışmanın amacı; hız, derlenebilirlik ve çalışma süresi açısından basit ve net bir benchmark sunmak.

## Kullanılan Modeller
- qwen2.5-coder  
- deepseek-coder-v2  
- gpt-oss  

## Nasıl Test Ediliyor?
- Python kodu modele veriliyor  
- C++ çıktısı üretiliyor  
- clang++ ile derleniyor  
- Çalıştırılıp süre ölçülüyor  

## Sonuçlar

Model              | Convert Time | Run Time
-------------------|-------------|---------
qwen2.5-coder     | 11.45s      | -
deepseek-coder-v2 | 14.55s      | 0.83s
gpt-oss           | 213.52s     | 0.86s

## Kısa Yorum
- deepseek en dengeli model  
- gpt-oss doğru ama çok yavaş  
- qwen hızlı ama compile edemiyor  
