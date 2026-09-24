#include <cstdio>
#include <cstdint>
#include <chrono>

// Fast path specialized for (param1=4, param2=1)
// Uses the identity: 1/(4i+1) - 1/(4i-1) = -2/(16i^2 - 1)
static inline double calculate(uint64_t iterations, int param1, int param2) {
    if (param1 == 4 && param2 == 1) {
        double result = 1.0;
        uint64_t n = iterations;

        // d = 16*i^2 - 1 at i=1, delta = d_{i+1} - d_i = 32*i + 16 (starts at i=1 -> 48)
        uint64_t d = 15;
        uint64_t delta = 48;

        const uint64_t blocks = n / 8;
        for (uint64_t k = 0; k < blocks; ++k) {
            result -= 2.0 / (double)d; d += delta; delta += 32;
            result -= 2.0 / (double)d; d += delta; delta += 32;
            result -= 2.0 / (double)d; d += delta; delta += 32;
            result -= 2.0 / (double)d; d += delta; delta += 32;
            result -= 2.0 / (double)d; d += delta; delta += 32;
            result -= 2.0 / (double)d; d += delta; delta += 32;
            result -= 2.0 / (double)d; d += delta; delta += 32;
            result -= 2.0 / (double)d; d += delta; delta += 32;
        }

        const uint64_t rem = n & 7u;
        for (uint64_t r = 0; r < rem; ++r) {
            result -= 2.0 / (double)d; d += delta; delta += 32;
        }
        return result;
    } else {
        // Generic fallback matching the Python order of operations
        double result = 1.0;
        for (uint64_t i = 1; i <= iterations; ++i) {
            int64_t j = (int64_t)i * (int64_t)param1 - (int64_t)param2;
            result -= 1.0 / (double)j;
            j = (int64_t)i * (int64_t)param1 + (int64_t)param2;
            result += 1.0 / (double)j;
        }
        return result;
    }
}

int main() {
    using clock = std::chrono::steady_clock;
    auto start = clock::now();

    double result = calculate(200000000ull, 4, 1) * 4.0;

    auto end = clock::now();
    double seconds = std::chrono::duration<double>(end - start).count();

    std::printf("Result: %.12f\n", result);
    std::printf("Execution Time: %.6f seconds\n", seconds);
    return 0;
}