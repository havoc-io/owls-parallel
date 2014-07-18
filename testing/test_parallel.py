# System imports
import unittest
from subprocess import check_call
from tempfile import mkdtemp

# owls-cache imports
from owls_cache.persistent import set_persistent_cache
from owls_cache.persistent.caches.fs import FileSystemPersistentCache

# owls-parallel imports
from owls_parallel import parallelized, ParallelizedEnvironment
from owls_parallel.backends.batch import BatchParallelizationBackend, \
    qsub_submit, qsub_monitor
from owls_parallel.backends.multiprocessing import \
    MultiprocessingParallelizationBackend
from owls_parallel.backends.ipython import IPythonParallelizationBackend
from owls_parallel.testing import counter, computation


computation.__name__ = 'owls_parallel.testing.computation'


# Create and set the global persistent cache
set_persistent_cache(FileSystemPersistentCache(mkdtemp()))


# Set up the multiprocessing backend
multiprocessing_backend = MultiprocessingParallelizationBackend()


# Try to set up the IPython backend, which may fail if an IPython cluster is
# not available
try:
    ipython_backend = IPythonParallelizationBackend()
except:
    ipython_backend = None


# Try to set up the batch backend, but only if the qsub command is available
try:
    check_call(['qstat'])
    batch_backend = BatchParallelizationBackend(mkdtemp(),
                                                qsub_submit,
                                                qsub_monitor,
                                                5)
except:
    batch_backend = None


class TestParallelizationBase(unittest.TestCase):
    def execute(self):
        # Reset the counter
        global counter
        counter = 0

        # Create a parallelization environment with the current backend
        parallel = ParallelizedEnvironment(self._backend)

        # Run the computation a few times in the parallelized environment
        while parallel.run():
            x = computation(1, 2)
            y = computation(3, 4)
            z = computation(5, 6)

        # Make sure the computation was never invoked locally
        self.assertEqual(counter, 0)

        # Validate the results
        self.assertEqual(x, 3)
        self.assertEqual(y, 7)
        self.assertEqual(z, 11)


class TestMultiprocessingParallelization(TestParallelizationBase):
    def setUp(self):
        self._backend = multiprocessing_backend

    def test(self):
        self.execute()


@unittest.skipIf(ipython_backend is None, 'IPython cluster not available')
class TestIPythonParallelization(TestParallelizationBase):
    def setUp(self):
        self._backend = ipython_backend

    def test(self):
        self.execute()


@unittest.skipIf(batch_backend is None, 'Batch cluster not available')
class TestBatchParallelization(TestParallelizationBase):
    def setUp(self):
        self._backend = batch_backend

    def test(self):
        self.execute()


# Run the tests if this is the main module
if __name__ == '__main__':
    unittest.main()