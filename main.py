#%%
# Gerekli kütüphaneleri import ediyoruz.
import time
import os
import io
import sys
import gradio as gr
import subprocess
from openai import OpenAI

#%%
# Ollama, OpenAI API'siyle birebir uyumlu bir endpoint sunuyor.
# Bu sayede OpenAI SDK'sını hiç değiştirmeden yerel modellere yönlendirebiliyoruz.
# api_key burada sembolik — Ollama kimlik doğrulaması gerektirmiyor.
ollama = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")

# %%
# Test edilecek modeller ve her birine karşılık gelen client tanımları.
# Şu an üçü de Ollama üzerinden çalışıyor; ileride farklı provider'lar eklendiğinde bu yapı genişletilebilir.
models = ["qwen2.5-coder", "deepseek-coder-v2", "gpt-oss"]
clients = {"qwen2.5-coder": ollama, "deepseek-coder-v2": ollama, "gpt-oss": ollama}

#%%
# Sistem özelliklerini dinamik olarak çekiyoruz.
# Bu bilgi (CPU, çekirdek sayısı vs.) LLM'e verilerek daha iyi optimize edilmiş C++ üretmesi sağlanır.
# Özellikle -mcpu=native gibi flag'lerle birlikte düşünüldüğünde modelin donanıma özel optimizasyon yapması hedeflenir.
from system_infos import retrieve_system_info

system_info = retrieve_system_info()
system_info

# %%
# C++ derleme komutu
# Burada maksimum performans hedefleniyor:
# -Ofast        : Agresif optimizasyonlar (bazı standart garantilerden feragat eder)
# -mcpu=native  : Mevcut CPU mimarisine özel optimize eder
# -flto=thin    : Link-time optimization (binary seviyesinde ekstra optimizasyon)
# -DNDEBUG      : Debug kontrollerini kaldırır (daha hızlı runtime)
compile_command = ["clang++", "-std=c++17", "-Ofast", "-mcpu=native", "-flto=thin", "-fvisibility=hidden", "-DNDEBUG", "main.cpp", "-o", "main"]

# Derlenen binary'nin çalıştırılması
run_command = ["./main"]

# %%
# Modele verdiğimiz görev tanımı. Kısa ve net tutuyoruz: yalnızca C++ kodu, sıfır açıklama, birebir aynı çıktı. 
# Modelin "yaratıcı" davranmasına izin vermek istemiyoruz. Bu çalışmada doğruluk ve hız tek kriter...
system_prompt = """
Your task is to convert Python code into high performance C++ code.
Respond only with C++ code. Do not provide any explanation other than occasional comments.
The C++ response needs to produce an identical output in the fastest possible time.
"""

# Sistem bilgisini ve derleme komutunu prompt'a gömerek modelin çıktısını doğrudan bu ortama uygun üretmesini istiyoruz.
# "Dosyaya yazılıp derleneceğini" açıkça belirtmek, modelin kod bloğu dışında herhangi bir metin üretmemesini pekiştiriyor.
def user_prompt_for(python):
    return f"""
Port this Python code to C++ with the fastest possible implementation that produces identical output in the least time.
The system information is:
{system_info}
Your response will be written to a file called main.cpp and then compiled and executed; the compilation command is:
{compile_command}
Respond only with C++ code.
Python code to port:

```python
{python}
```
"""

# %%
# OpenAI chat formatına uygun mesaj listesini oluşturuyoruz.
# System prompt + user prompt ikili yapısı, modelin bağlamı doğru kurmasını ve rolünü korumasını sağlıyor.
def messages_for(python):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_for(python)}
    ]

# %%
# Modelin ürettiği C++ kodunu diske yazdırıyoruz.
# Dosya adını sabit tutarak derleme komutunu değiştirmek zorunda kalmıyoruz.
def write_output(cpp):
    with open("main.cpp", "w") as f:
        f.write(cpp)

# %%
# Çeviri pipeline'ının kalbi burada.
# GPT ailesi modeller reasoning_effort parametresini desteklediğinden onlara "high" geçiyoruz 
# Ollama modelleri bu parametreyi tanımıyor, dolayısıyla None ile atlıyoruz.
# Modelin yanıtından markdown kod bloğu işaretlerini temizleyerek doğrudan derlenebilir bir .cpp dosyası elde ediyoruz.
def port(model, python):
    client = clients[model]

    start = time.time()

    reasoning_effort = "high" if 'gpt' in model else None
    response = client.chat.completions.create(
        model=model,
        messages=messages_for(python),
        reasoning_effort=reasoning_effort
    )

    end = time.time()
    convert_time = end - start

    reply = response.choices[0].message.content
    reply = reply.replace('```cpp','').replace('```','')

    # C++ kodunun başına metadata ekle
    header = f'''
// Model: {model}
// Convert Time: {convert_time:.4f} seconds
'''

    reply = header + reply
    write_output(reply)
    return reply

# %%
# Benchmark olarak Leibniz serisiyle π hesaplama algoritmasını kullanıyoruz.
# 200 milyon iterasyon kasıtlı olarak tanımlandı. 
# Python'un bu yükü ne kadar ağır taşıdığını, C++'ın ise ne kadar hızlı bitireceğini somut sayılarla görmek istiyoruz.
# Bu kod string olarak tutuluyor çünkü hem exec() ile çalıştırılacak hem de LLM'e port edilmek üzere prompt'a gönderilecek.
pi = """
import time

def calculate(iterations, param1, param2):
    result = 1.0
    for i in range(1, iterations+1):
        j = i * param1 - param2
        result -= (1/j)
        j = i * param1 + param2
        result += (1/j)
    return result

start_time = time.time()
result = calculate(200_000_000, 4, 1) * 4
end_time = time.time()

print(f"Result: {result:.12f}")
print(f"Execution Time: {(end_time - start_time):.6f} seconds")
"""

# %%
# Python kodunu aynı süreçte, izole bir namespace içinde çalıştırıyoruz.
# stdout'u geçici olarak bir StringIO buffer'a yönlendirerek çıktıyı Gradio arayüzüne taşıyabilecek şekilde yakalıyoruz.
def run_python(code):
    globals_dict = {"__builtins__": __builtins__}

    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer

    try:
        exec(code, globals_dict)
        output = buffer.getvalue()
    except Exception as e:
        output = f"Error: {e}"
    finally:
        sys.stdout = old_stdout

    return output

#%%
# Derleme ve çalıştırma adımlarını tek fonksiyonda topluyoruz.
# Binary'yi üç kez çalıştırıyoruz...
# İlk çalışmada CPU cache soğuk olabilir. Sonraki ölçümler daha kararlı sonuç verir.
def compile_and_run():
    try:
        subprocess.run(compile_command, check=True, text=True, capture_output=True)
        print(subprocess.run(run_command, check=True, text=True, capture_output=True).stdout)
        print(subprocess.run(run_command, check=True, text=True, capture_output=True).stdout)
        print(subprocess.run(run_command, check=True, text=True, capture_output=True).stdout)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred:\n{e.stderr}")

# %%
# Gradio arayüzünü tanımlıyoruz. 
# Sol panel Python kodunu, sağ panel ise modelin ürettiği C++ çıktısını gösteriyor. 
# 28 satır yükseklik uzun kodlar için yeterli görünürlük sağlıyor.
# Model seçimi dropdown'dan yapılıyor; 
# "Convert" butonuna basıldığında port() fonksiyonu tetikleniyor ve C++ kodu sağ panele dolduruluyor.
with gr.Blocks() as ui:
    with gr.Row():
        python = gr.Textbox(label="Python code:", lines=28, value=pi)
        cpp = gr.Textbox(label="C++ code:", lines=28)
    with gr.Row():
        model = gr.Dropdown(models, label="Select model", value=models[0])
        convert = gr.Button("Convert code")

    convert.click(port, inputs=[model, python], outputs=[cpp])

# inbrowser=True ile uygulama ayağa kalkar kalkmaz varsayılan tarayıcıda açılır.
ui.launch(inbrowser=True)

#%%
# Arayüzden bağımsız olarak derleme + çalıştırma döngüsünü doğrudan notebook'tan tetikleyebiliyoruz. 
# Gradio olmadan hızlı test atmak için kullanışlı.
compile_and_run()

#%%

# Model: qwen2.5-coder
# Convert Time: 11.4518 seconds
# Run Time: ERROR

# Model: deepseek-coder-v2
# Convert Time: 14.5489 seconds
# Run Time: 0.833225197 seconds

# Model: gpt-oss
# Convert Time: 213.5196 seconds
# Run Time: 0.860282 seconds