export function chunks<T>(array: T[], size: number): T[][] {
  return [...new Array(Math.ceil(array.length / size)).keys()].map((_, index) =>
    array.slice(index * size, (index + 1) * size),
  );
}
