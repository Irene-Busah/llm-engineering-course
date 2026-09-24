use std::time::Instant;

// Linear Congruential Generator with 32-bit wrapping arithmetic
struct Lcg {
    value: u32,
}

impl Lcg {
    #[inline(always)]
    fn new(seed: u32) -> Self {
        Self { value: seed }
    }

    #[inline(always)]
    fn next_u32(&mut self) -> u32 {
        // Parameters: a = 1664525, c = 1013904223, m = 2^32
        self.value = self.value.wrapping_mul(1664525).wrapping_add(1013904223);
        self.value
    }
}

// Kadane's algorithm for maximum subarray sum, streaming the RNG (identical result to naive O(n^2))
#[inline(always)]
fn max_subarray_sum(n: usize, seed: u32, min_val: i128, max_val: i128) -> i128 {
    let mut lcg = Lcg::new(seed);
    let width = (max_val - min_val + 1) as u32;

    let mut first = true;
    let mut best: i128 = 0;
    let mut ending: i128 = 0;

    let mut i = 0usize;
    while i < n {
        let r = lcg.next_u32();
        let val = (r % width) as i128 + min_val;

        if first {
            ending = val;
            best = val;
            first = false;
        } else {
            let sum = ending + val;
            ending = if sum > val { sum } else { val };
            if ending > best {
                best = ending;
            }
        }

        i += 1;
    }

    best
}

#[inline(always)]
fn total_max_subarray_sum(n: usize, initial_seed: u32, min_val: i128, max_val: i128) -> i128 {
    let mut total: i128 = 0;
    let mut lcg = Lcg::new(initial_seed);
    let mut runs = 0;
    while runs < 20 {
        let seed = lcg.next_u32();
        total += max_subarray_sum(n, seed, min_val, max_val);
        runs += 1;
    }
    total
}

fn main() {
    // Parameters
    let n: usize = 10000;
    let initial_seed: u32 = 42;
    let min_val: i128 = -10;
    let max_val: i128 = 10;

    // Timing
    let start_time = Instant::now();
    let result = total_max_subarray_sum(n, initial_seed, min_val, max_val);
    let elapsed = start_time.elapsed().as_secs_f64();

    println!("Total Maximum Subarray Sum (20 runs): {}", result);
    println!("Execution Time: {:.6} seconds", elapsed);
}