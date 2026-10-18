"""Independent reference outputs from the installed NumPy PCG64 bit generator."""
import json
from pathlib import Path
import random
import numpy as np

OUT = Path(__file__).resolve().parent


def main():
    cases = [(0, 1), (1, 3), (2**128 - 1, 2**128 - 1)]
    chooser = random.Random(20261018)
    cases += [(chooser.getrandbits(128), chooser.getrandbits(128) | 1) for _ in range(97)]
    reference = []
    for state, increment in cases:
        initial = {'bit_generator': 'PCG64', 'state': {'state': state, 'inc': increment},
                   'has_uint32': 0, 'uinteger': 0}
        raw = np.random.PCG64(0)
        raw.state = initial
        uniform = np.random.PCG64(0)
        uniform.state = initial
        reference.append({'state': str(state), 'increment': str(increment),
                          'raw': [str(v) for v in raw.random_raw(8)],
                          'uniform': np.random.Generator(uniform).random(8).tolist()})
    result = {'schema': 'FS_PCG64_NUMPY_EXPLICIT_STATE_REFERENCE_V1',
              'numpy_version': np.__version__,
              'reference': 'https://numpy.org/doc/stable/reference/random/bit_generators/pcg64.html',
              'seed_compatibility': 'Explicit state/increment only; not NumPy SeedSequence compatibility',
              'cases': reference, 'gold_lock': False}
    (OUT / 'numpy-vectors.json').write_text(json.dumps(result, indent=2) + '\n')
    print(f'NumPy {np.__version__}: {len(cases)} states, 800 uint64 and 800 double reference outputs')


if __name__ == '__main__':
    main()
