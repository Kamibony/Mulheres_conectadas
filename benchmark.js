const mockGetDoc = async (uid) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ exists: () => true, data: () => ({ identity: `identity_${uid}` }) });
    }, 50); // simulate 50ms network latency
  });
};

const users = ['user1', 'user2', 'user3', 'user4', 'user5'];

const runSequential = async () => {
  const start = performance.now();
  const newIdentities = {};
  for (const uid of users) {
    const identityDoc = await mockGetDoc(uid);
    if (identityDoc.exists()) {
      newIdentities[uid] = identityDoc.data().identity;
    }
  }
  const end = performance.now();
  return end - start;
};

const runParallel = async () => {
  const start = performance.now();
  const newIdentities = {};
  await Promise.all(
    users.map(async (uid) => {
      const identityDoc = await mockGetDoc(uid);
      if (identityDoc.exists()) {
        newIdentities[uid] = identityDoc.data().identity;
      }
    })
  );
  const end = performance.now();
  return end - start;
};

const runBenchmark = async () => {
  console.log('Running benchmark...');
  const seqTimes = [];
  const parTimes = [];

  for (let i = 0; i < 5; i++) {
    seqTimes.push(await runSequential());
    parTimes.push(await runParallel());
  }

  const avgSeq = seqTimes.reduce((a, b) => a + b, 0) / seqTimes.length;
  const avgPar = parTimes.reduce((a, b) => a + b, 0) / parTimes.length;

  console.log(`Average Sequential Time: ${avgSeq.toFixed(2)} ms`);
  console.log(`Average Parallel Time: ${avgPar.toFixed(2)} ms`);
  console.log(`Speedup: ${(avgSeq / avgPar).toFixed(2)}x`);
};

runBenchmark();
