/** Element by id. The page markup guarantees the id exists, so a miss is a bug and throws at first use. */
export const $ = <T extends Element = HTMLElement>(id: string) => document.getElementById(id) as unknown as T;
