import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import vm from 'node:vm'
import ts from 'typescript'

const source = readFileSync(new URL('../src/useSelectedEntity.ts', import.meta.url), 'utf8')
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS },
}).outputText

function harness() {
  let state = null
  let effect
  let cleanup
  const requests = []
  const timers = new Map()
  const cleared = []
  const exports = {}
  vm.runInNewContext(compiled, {
    exports, AbortController, console,
    require: () => ({
      useState: () => [state, value => { state = value }],
      useEffect: fn => { effect = fn },
    }),
    fetch: (url, options) => new Promise(resolve => requests.push({ url, ...options, resolve })),
    setTimeout: fn => { const id = Symbol(); timers.set(id, fn); return id },
    clearTimeout: id => timers.delete(id),
  })
  const clear = id => cleared.push(id)
  return {
    requests, timers, cleared,
    render: url => exports.default(url, clear),
    commit: () => { cleanup?.(); cleanup = effect() },
    unmount: () => cleanup?.(),
  }
}

const flush = () => new Promise(resolve => setImmediate(resolve))
const response = data => ({ ok: true, status: 200, json: async () => data })

test('selection changes hide old data and ignore late responses', async () => {
  const h = harness()
  assert.equal(h.render(null), null)
  h.render('/monkeys/1'); h.commit()
  h.requests[0].resolve(response({ id: 1 })); await flush()
  assert.equal(h.render('/monkeys/1').id, 1)
  assert.equal(h.render('/monkeys/2'), null)
  h.commit()
  assert.equal(h.requests[0].signal.aborted, true)
  h.requests[1].resolve(response({ id: 2 })); await flush()
  assert.equal(h.render('/monkeys/2').id, 2)
  h.unmount()

  const late = harness()
  late.render('/tourists/1'); late.commit()
  late.render('/tourists/2'); late.commit()
  late.requests[1].resolve(response({ id: 2 })); await flush()
  late.requests[0].resolve(response({ id: 1 })); await flush()
  assert.equal(late.render('/tourists/2').id, 2)
  late.unmount()
})

test('404 clears removed entities and stops polling', async () => {
  for (const kind of ['monkeys', 'tourists']) {
    const h = harness()
    h.render(`/${kind}/1`); h.commit()
    h.requests[0].resolve({ status: 404 }); await flush()
    assert.equal(h.cleared.length, 1)
    assert.equal(h.cleared[0], null)
    assert.equal(h.render(`/${kind}/1`), null)
    assert.equal(h.timers.size, 0)
    h.unmount()
  }
})

test('polling waits for completion and cleanup cancels pending work', async () => {
  const h = harness()
  h.render('/monkeys/1'); h.commit()
  assert.equal(h.timers.size, 0)
  h.requests[0].resolve(response({ id: 1 })); await flush()
  assert.equal(h.timers.size, 1)
  h.unmount()
  assert.equal(h.timers.size, 0)

  const pending = harness()
  pending.render('/tourists/1'); pending.commit(); pending.unmount()
  pending.requests[0].resolve(response({ id: 1 })); await flush()
  assert.equal(pending.render('/tourists/1'), null)
  assert.equal(pending.timers.size, 0)
})
