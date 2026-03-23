
// Model: qwen2.5-coder
// Convert Time: 11.4518 seconds


#include <iostream>
#include <chrono>

double calculate(int iterations, int param1, int param2) {
    double result = 1.0;
    for (int i = 1; i <= iterations; ++i) {
        double j = static_cast<double>(i * param1 - param2);
        result -= (1.0 / j);
        j = static_cast<double>(i * param1 + param2);
        result += (1.0 / j);
    }
    return result;
}

int main() {
    auto start_time = std::chrono::high_resolution_clock::now();
    double result = calculate(200000000, 4, 1) * 4;
    auto end_time = std::chrono::high_resolution_clock::now();

    std::cout << "Result: " << std::fixed << std::setprecision(12) << result << "\n";
    std::cout << "Execution Time: " 
              << std::chrono::duration_cast<std::chrono::duration<double>>(end_time - start_time).count()
              << " seconds\n";

    return 0;
}

