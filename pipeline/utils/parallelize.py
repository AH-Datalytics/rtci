from multiprocessing.pool import ThreadPool
from tqdm import tqdm


def thread(worker, jobs, threads=5):
    pool = ThreadPool(threads)
    results = list()
    for result in tqdm(pool.imap_unordered(worker, jobs), total=len(jobs)):
        if result and isinstance(result, list):
            results.extend([r for r in result if r])
        elif result:
            results.append(result)
    pool.close()
    pool.join()
    if results:
        return results
