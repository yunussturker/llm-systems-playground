
// Model: gpt-oss
// Convert Time: 213.5196 seconds
#include <iostream>
#include <iomanip>
#include <chrono>
#include <cstdint>

int main() {
    constexpr std::size_t iterations = 200'000'000;
    double result = 1.0;
    double j1 = 3.0; // 4*1 - 1
    double j2 = 5.0; // 4*1 + 1

    using namespace std::chrono;
    auto start = high_resolution_clock::now();

    for (std::size_t n = 0; n < iterations; ++n) {
        result -= 1.0 / j1;
        result += 1.0 / j2;
        j1 += 4.0;
        j2 += 4.0;
    }

    result *= 4.0;

    auto end = high_resolution_clock::now();
    double elapsed = duration<double>(end - start).count();

    std::cout << std::fixed << std::setprecision(12);
    std::cout << "Result: " << result << "\n";
    std::cout << std::fixed << std::setprecision(6);
    std::cout << "Execution Time: " << elapsed << " seconds\n";
    return 0;
}
