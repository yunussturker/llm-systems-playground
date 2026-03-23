
// Model: deepseek-coder-v2
// Convert Time: 14.5489 seconds
 
#include <iostream>
#include <chrono>

double calculate(int iterations, double param1, double param2) {
    double result = 1.0;
    for (int i = 1; i <= iterations; ++i) {
        int j = i * param1 - param2;
        result -= (1.0 / j);
        j = i * param1 + param2;
        result += (1.0 / j);
    }
    return result;
}

int main() {
    auto start_time = std::chrono::high_resolution_clock::now();
    double result = calculate(200'000'000, 4.0, 1.0) * 4;
    auto end_time = std::chrono::high_resolution_clock::now();
    
    std::cout.precision(12);
    std::cout << "Result: " << result << '\n';
    std::cout << "Execution Time: " << std::chrono::duration<double>(end_time - start_time).count() << " seconds\n";
    
    return 0;
}
