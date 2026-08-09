# Como contribuir

Obrigado por querer contribuir com a Pedaleira Digital. Este projeto ainda
está em fase inicial, então o fluxo abaixo é simples e pode evoluir conforme
o projeto cresce.

## Estrutura do repositório

Antes de contribuir, vale se situar em qual parte do projeto sua mudança se
encaixa:

- `firmware/stm32` — processamento digital de áudio (STM32H7xx)
- `firmware/esp32` — comunicação MQTT / conectividade (ESP32)
- `docs/code` — documentação de firmware e software
- `docs/hardware` — esquemáticos e documentação de hardware
- `docs/components` — datasheets dos componentes utilizados

## Fluxo de contribuição

1. Abra uma issue descrevendo o problema ou a melhoria antes de começar a
   codar, para alinhar o escopo.
2. Crie um branch a partir de `development` (branch de desenvolvimento ativo
   — `master` segue outro fluxo), com um nome que descreva a mudança
   (ex.: `feat/eq-parametrica`, `fix/ruido-adc`).
3. Faça commits pequenos e com mensagens no padrão
   [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` nova funcionalidade
   - `fix:` correção de bug
   - `docs:` mudanças de documentação
   - `chore:` manutenção, reorganização, build
   - `refactor:` mudança de código sem alterar comportamento
4. Abra um Pull Request para `development` explicando o que mudou e por quê.
   Referencie a issue relacionada, se houver.

## Diretrizes de código

- **Firmware STM32**: projeto STM32CubeIDE. Ao alterar periféricos, atualize
  o `.ioc` e regenere o código pela ferramenta em vez de editar os arquivos
  gerados manualmente.
- Mantenha o código gerado pela HAL/CubeMX separado do código de aplicação
  sempre que possível.
- Evite adicionar dependências ou abstrações sem necessidade — este é um
  projeto embarcado com recursos limitados.

## Dúvidas

Abra uma issue com sua dúvida ou sugestão.
