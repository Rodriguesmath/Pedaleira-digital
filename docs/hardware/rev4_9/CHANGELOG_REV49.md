# Alterações 4.8 → 4.9

- Originais 4.8 e firmware preservados antes das mudanças.
- Eliminados TC1044S e rede de tensão negativa; alimentação proposta de 12 V simples, após rejeitar 9 V para a margem exigida.
- CW7805 mantido nominalmente, com identidade/pinagem/térmica pendentes; fonte comum de 5 V com ramais separados e dissipador dimensionado.
- Referências OP e ADC independentes; VCOM não carrega circuitos externos.
- ADC com sinais complementares, acoplamento bipolar, proteção de transientes e filtro recalculado. A impedância de fonte maior exige qualificação com o codec real.
- Receptor DAC polarizado em VREF_OP, ganho 0,499; filtro 220 Ω/2,2 nF e C5 com polaridade definida.
- Entrada de guitarra protegida por resistor e dois diodos por sentido, evitando compressão do clamp simples no nível nominal.
- Onze TP, tabelas integrais, BOM elétrica/complementar e planos para perfboard.
- PLL1 corrigida: VCO de 1100 MHz fora do máximo 836 MHz, substituído por 550 MHz com CPU preservada a 550 MHz (M5/N110/P1).
- Firmware: AF8 de PE4/5/6, reset LOW, timeout/pós-reset, 03h=39h, 06h=14h, mute inicial e SW4 mute. PE15 deixa de ser togglado pelo heartbeat. Transporte permanece bloqueado; não foi inventada uma implementação SAI/BDMA.
- ERC sem violações; netlists/BOM/PDF/grafo visível comparados; OP/AC/transientes executados; 9 testes existentes e teste DSP nativo passaram.
- Veredito negativo explícito devido às pendências de especificação e implementação; sem teste físico ou alegação de áudio comprovado.
