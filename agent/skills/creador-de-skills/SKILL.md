---
name: creador-de-skills
description: crea nuevos skills para antigravity con una estructura estandarizada, predecible y fácil de mantener.
---
# Creador de Skills

## Cuándo usar este skill
- Cuando el usuario pida "crear un skill nuevo" o "créame un skill para X".
- Cuando el usuario repita un proceso que pueda ser estandarizado.
- Cuando se necesite un estándar de formato para operacionalizar una tarea.
- Cuando haya que convertir un prompt largo en un procedimiento reutilizable.

## Inputs necesarios
- Propósito o meta del nuevo skill.
- Pasos, heurísticas o plantillas que debe usar el nuevo skill.
- Nivel de libertad deseado (Alta, Media o Baja).

## Workflow
### 1) Plan (Validar requisitos)
- Entender el objetivo final del skill solicitado.
- Determinar si requiere recursos adicionales (scripts, plantillas, ejemplos).
- Definir el nivel de libertad adecuado:
  - Alta libertad (heurísticas): para brainstorming, ideas, alternativas.
  - Media libertad (plantillas): para documentos, copys, estructuras.
  - Baja libertad (pasos exactos / comandos): para operaciones frágiles, scripts, cambios técnicos.

### 2) Ejecución (Redactar contenido)
- Crear el `name` (corto, minúsculas, guiones, sin nombres de herramientas salvo que sea imprescindible).
- Crear la `description` (español, tercera persona, máximo 220 caracteres, clara sobre qué hace y cuándo usarlo).
- Redactar el contenido siguiendo los principios: sin relleno, pocas reglas pero claras, y roles separados.
- Definir triggers y workflow del nuevo skill.

### 3) Revisión (Verificar checklist)
- [ ] Entendí el objetivo final.
- [ ] Tengo inputs necesarios.
- [ ] Definí output exacto.
- [ ] Apliqué restricciones (YAML correcto, sin estilo blog).
- [ ] Revisé coherencia y errores.

## Instrucciones
Eres un experto en diseñar Skills para el entorno de Antigravity. Tu objetivo es crear Skills predecibles, reutilizables y fáciles de mantener, con una estructura clara de carpetas y una lógica que funcione bien en producción.

Reglas fundamentales de escritura:
1. **Claridad sobre longitud:** Mejor pocas reglas, pero muy claras. Evita explicaciones tipo blog. El skill es un manual de ejecución.
2. **Separación de responsabilidades:** Si hay "estilo", va a un recurso. Si hay "pasos", van al workflow.
3. **Pedir datos:** Si un input es crítico para ejecutar el skill, haz que pregunte por él.
4. **Salida estandarizada:** Define exactamente qué formato devuelve el nuevo skill (lista, tabla, JSON, markdown).

Manejo de errores y correcciones:
- Si el output no cumple el formato, vuelve al paso de Ejecución, ajusta restricciones y re-genera.
- Si hay ambigüedad, pide feedback al usuario y pregunta antes de asumir.

## Output (formato exacto)
Tu salida al usar este skill SIEMPRE debe incluir:
1. La ruta de carpeta del skill dentro de `agent/skills/`
2. El contenido completo de SKILL.md con frontmatter YAML
3. Cualquier recurso adicional (scripts/recursos/ejemplos) solo si aporta valor real

Devuelve la información utilizando este formato exacto:

Carpeta
`agent/skills/<nombre-del-skill>/`

SKILL.md
```markdown
---
name: ...
description: ...
---
# <Título del skill>
## Cuándo usar este skill
- ...
- ...

## Inputs necesarios
- ...
- ...

## Workflow
1) ...
2) ...
3) ...

## Instrucciones
...

## Output (formato exacto)
...
```

Recursos opcionales (solo si aportan valor)
- `recursos/<archivo>.md`
- `scripts/<archivo>.sh`

*(Opcional) Sugerencias adicionales:* Si el usuario está creando skills útiles, sugiere ideas adicionales como:
- Skill de "estilo y marca"
- Skill de "planificar vídeos"
- Skill de "auditar landing"
- Skill de "debug de app"
- Skill de "responder emails con tono"
