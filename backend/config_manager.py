"""
Gerenciador de Configurações da Triagem Automática
Carrega, valida e gerencia as configurações do arquivo triagem_config.json
"""

import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TriagemConfig:
    """Classe que representa as configurações de triagem"""
    version: str
    metadata: Dict[str, Any]
    thresholds: Dict[str, int]
    pesos_categorias: Dict[str, float]
    pontuacao_criterios: Dict[str, Any]
    limites_conteudo: Dict[str, int]
    palavras_chave: Dict[str, Any]
    formatos_anexos_aceitos: list
    configuracoes_avancadas: Dict[str, Any]

class ConfigManager:
    """Gerenciador de configurações da triagem automática"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa o gerenciador de configurações
        
        Args:
            config_path: Caminho para o arquivo de configuração (opcional)
        """
        # Define o caminho padrão do arquivo de configuração
        if config_path is None:
            current_dir = Path(__file__).parent
            config_path = current_dir / "triagem_config.json"
        
        self.config_path = Path(config_path)
        self._config: Optional[TriagemConfig] = None
        self._last_modified: Optional[float] = None
        
        # Carrega as configurações iniciais
        self.reload_config()
    
    def reload_config(self) -> bool:
        """
        Recarrega as configurações do arquivo JSON
        
        Returns:
            bool: True se recarregou com sucesso, False caso contrário
        """
        try:
            if not self.config_path.exists():
                logger.error(f"Arquivo de configuração não encontrado: {self.config_path}")
                return False
            
            # Verifica se o arquivo foi modificado
            current_modified = self.config_path.stat().st_mtime
            if self._last_modified and current_modified == self._last_modified:
                return True  # Não há mudanças
            
            # Carrega o arquivo JSON
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Valida a estrutura básica
            if not self._validate_config_structure(config_data):
                logger.error("Estrutura do arquivo de configuração inválida")
                return False
            
            # Cria o objeto de configuração
            self._config = TriagemConfig(
                version=config_data.get('version', '1.0'),
                metadata=config_data.get('metadata', {}),
                thresholds=config_data.get('thresholds', {}),
                pesos_categorias=config_data.get('pesos_categorias', {}),
                pontuacao_criterios=config_data.get('pontuacao_criterios', {}),
                limites_conteudo=config_data.get('limites_conteudo', {}),
                palavras_chave=config_data.get('palavras_chave', {}),
                formatos_anexos_aceitos=config_data.get('formatos_anexos_aceitos', []),
                configuracoes_avancadas=config_data.get('configuracoes_avancadas', {})
            )
            
            self._last_modified = current_modified
            logger.info(f"Configurações carregadas com sucesso de {self.config_path}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear JSON: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {e}")
            return False
    
    def _validate_config_structure(self, config_data: Dict[str, Any]) -> bool:
        """
        Valida a estrutura básica do arquivo de configuração
        
        Args:
            config_data: Dados carregados do JSON
            
        Returns:
            bool: True se a estrutura é válida
        """
        required_sections = [
            'thresholds', 'pesos_categorias', 'pontuacao_criterios', 
            'limites_conteudo'
        ]
        
        for section in required_sections:
            if section not in config_data:
                logger.error(f"Seção obrigatória ausente: {section}")
                return False
        
        # Valida thresholds
        thresholds = config_data.get('thresholds', {})
        required_thresholds = ['aprovacao_automatica', 'revisao_humana', 'recusa_automatica']
        for threshold in required_thresholds:
            if threshold not in thresholds:
                logger.error(f"Threshold obrigatório ausente: {threshold}")
                return False
        
        # Valida pesos (devem somar 1.0)
        pesos = config_data.get('pesos_categorias', {})
        total_pesos = sum(pesos.values())
        if abs(total_pesos - 1.0) > 0.01:  # Tolerância de 1%
            logger.warning(f"Soma dos pesos não é 1.0: {total_pesos}")
        
        return True
    
    @property
    def config(self) -> TriagemConfig:
        """
        Retorna as configurações atuais (com hot-reload automático)
        
        Returns:
            TriagemConfig: Configurações atuais
        """
        # Verifica se precisa recarregar
        if self.config_path.exists():
            current_modified = self.config_path.stat().st_mtime
            if self._last_modified != current_modified:
                logger.info("Arquivo de configuração modificado, recarregando...")
                self.reload_config()
        
        if self._config is None:
            raise RuntimeError("Configurações não carregadas. Verifique o arquivo de configuração.")
        
        return self._config
    
    # Métodos de conveniência para acessar configurações específicas
    
    def get_threshold(self, tipo: str) -> int:
        """Retorna um threshold específico"""
        return self.config.thresholds.get(tipo, 50)
    
    def get_peso_categoria(self, categoria: str) -> float:
        """Retorna o peso de uma categoria específica"""
        return self.config.pesos_categorias.get(categoria, 0.25)
    
    def get_pontuacao_criterio(self, categoria: str, criterio: str) -> int:
        """Retorna a pontuação de um critério específico"""
        categoria_config = self.config.pontuacao_criterios.get(categoria, {})
        criterios = categoria_config.get('criterios', {})
        criterio_config = criterios.get(criterio, {})
        return criterio_config.get('pontos', 0)
    
    def get_limite_conteudo(self, limite: str) -> int:
        """Retorna um limite de conteúdo específico"""
        return self.config.limites_conteudo.get(limite, 0)
    
    def get_palavras_chave(self, tipo: str) -> list:
        """Retorna palavras-chave de um tipo específico"""
        return self.config.palavras_chave.get(tipo, [])
    
    def is_formato_anexo_aceito(self, extensao: str) -> bool:
        """Verifica se um formato de anexo é aceito"""
        extensao_lower = extensao.lower()
        if not extensao_lower.startswith('.'):
            extensao_lower = '.' + extensao_lower
        return extensao_lower in self.config.formatos_anexos_aceitos
    
    def get_configuracao_avancada(self, secao: str, chave: str = None) -> Any:
        """Retorna uma configuração avançada específica"""
        secao_config = self.config.configuracoes_avancadas.get(secao, {})
        if chave is None:
            return secao_config
        return secao_config.get(chave)
    
    def save_config(self, backup: bool = True) -> bool:
        """
        Salva as configurações atuais no arquivo JSON
        
        Args:
            backup: Se deve criar backup antes de salvar
            
        Returns:
            bool: True se salvou com sucesso
        """
        try:
            if backup and self.config_path.exists():
                backup_path = self.config_path.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                backup_path.write_text(self.config_path.read_text(encoding='utf-8'), encoding='utf-8')
                logger.info(f"Backup criado: {backup_path}")
            
            # Prepara os dados para salvar
            config_dict = {
                'version': self._config.version,
                'metadata': {
                    **self._config.metadata,
                    'updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                'thresholds': self._config.thresholds,
                'pesos_categorias': self._config.pesos_categorias,
                'pontuacao_criterios': self._config.pontuacao_criterios,
                'limites_conteudo': self._config.limites_conteudo,
                'palavras_chave': self._config.palavras_chave,
                'formatos_anexos_aceitos': self._config.formatos_anexos_aceitos,
                'configuracoes_avancadas': self._config.configuracoes_avancadas
            }
            
            # Salva o arquivo
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configurações salvas em {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna um resumo das configurações atuais"""
        config = self.config
        return {
            'version': config.version,
            'arquivo': str(self.config_path),
            'ultima_modificacao': datetime.fromtimestamp(self._last_modified) if self._last_modified else None,
            'thresholds': config.thresholds,
            'total_criterios': sum(
                len(cat.get('criterios', {})) 
                for cat in config.pontuacao_criterios.values()
            ),
            'soma_pesos': sum(config.pesos_categorias.values()),
            'formatos_aceitos': len(config.formatos_anexos_aceitos)
        }

# Instância global do gerenciador de configurações
_config_manager = None

def get_config_manager() -> ConfigManager:
    """
    Retorna a instância global do gerenciador de configurações
    
    Returns:
        ConfigManager: Instância do gerenciador
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_triagem_config() -> TriagemConfig:
    """
    Função de conveniência para obter as configurações de triagem
    
    Returns:
        TriagemConfig: Configurações atuais
    """
    return get_config_manager().config

# Funções de conveniência para acessar configurações específicas
def get_threshold(tipo: str) -> int:
    """Retorna um threshold específico"""
    return get_config_manager().get_threshold(tipo)

def get_peso_categoria(categoria: str) -> float:
    """Retorna o peso de uma categoria específica"""
    return get_config_manager().get_peso_categoria(categoria)

def get_pontuacao_criterio(categoria: str, criterio: str) -> int:
    """Retorna a pontuação de um critério específico"""
    return get_config_manager().get_pontuacao_criterio(categoria, criterio)