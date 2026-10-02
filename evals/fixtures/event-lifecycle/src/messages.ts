type Listener = (message: string) => void
const listeners = new Set<Listener>()

export const messages = {
  subscribe(listener: Listener) {
    listeners.add(listener)
    return () => { listeners.delete(listener) }
  },
  publish(message: string) {
    for (const listener of listeners) listener(message)
  },
}
