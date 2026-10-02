import { isNavigationFailure, type Router } from 'vue-router'

export function createHistory(router: Router) {
  const history: string[] = []

  async function replaceTo(target: string) {
    history.push(router.currentRoute.value.fullPath)
    await router.replace(target)
  }

  async function replaceSafely(target: string) {
    const source = router.currentRoute.value.fullPath
    const failure = await router.replace(target)
    if (!isNavigationFailure(failure)) history.push(source)
  }

  return { history, replaceTo, replaceSafely }
}
