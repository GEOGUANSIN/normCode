### normtext

> Multiplication of two multi-digit natural numbers is performed through a digit-by-digit algorithm that generates and sums partial products. The process begins by decomposing both numbers, the multiplicand and the multiplier, into sequences of their individual digits based on their place value (ones, tens, hundreds, etc.).

> The core of the procedure involves iterating through each digit of the multiplier, starting from the rightmost (ones) digit. For each multiplier digit, a partial product is calculated by multiplying it with the entire multiplicand. This sub-step is itself a digit-by-digit operation where the product of any two single digits is determined by consulting a multiplication table. The result of this lookup is then handled by recording the ones digit of the product and carrying over the tens digit to the next column's calculation.

> A multiplication table is a two-dimensional grid used to define the multiplication operation for a set of numbers. The table is structured with rows and columns, each indexed by a sequence of natural numbers (e.g., 1 through 9). The cell at the intersection of any given row and column contains the product of the corresponding row and column index numbers.

> Each calculated partial product is then positionally shifted to the left based on the place value of the multiplier digit that generated it. The partial product from the multiplier's ones digit is not shifted, the one from the tens digit is shifted one place to the left (effectively multiplying it by 10), the one from the hundreds digit is shifted two places, and so on.

> Finally, all the positionally shifted partial products are summed together. The result of this final addition is the total product of the original two numbers.


