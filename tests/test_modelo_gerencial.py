#!/usr/bin/env python3
"""Testes do modelo não destrutivo com fontes oficiais versionadas."""
import copy
import json
import os
import sys
import tempfile
from jsonschema.exceptions import ValidationError
import unittest
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'scripts'))
from gerar_modelo_gerencial import get_snapshot
from validar_modelo_gerencial import validate

SOURCE_ROOT=Path(os.getenv('MODEL_REPO_ROOT',str(BASE))).resolve()
AUDIT=Path(os.environ['MODEL_AUDIT_PATH']).resolve() if 'MODEL_AUDIT_PATH' in os.environ else None

class ModeloGerencialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.internal=get_snapshot(SOURCE_ROOT,'interno',AUDIT)
        cls.public=get_snapshot(SOURCE_ROOT,'publico')
    def test_schema_and_reconciliation(self):
        self.assertTrue(validate(self.internal,SOURCE_ROOT)['valido'])
        self.assertTrue(validate(self.public,SOURCE_ROOT)['valido'])
    def test_trusted_events_preserved(self):
        self.assertEqual(len(self.internal['referencias_eventos']),60)
        self.assertEqual(self.internal['diagnostico']['registros_homologados_campo'],59)
        self.assertEqual(self.internal['diagnostico']['registros_homologados_a_reclassificar'],22)
        self.assertEqual(self.internal['diagnostico']['registros_pendentes_esclarecimento'],1)
        self.assertTrue(any(e['id']=='wa-20261117-0852-e07-camisas-ambiguo' and e['validacao_relato']=='pendente_esclarecimento' for e in self.internal['referencias_eventos']))
    def test_public_view_excludes_sensitive_and_pending_events(self):
        self.assertEqual(len(self.public['referencias_eventos']),45)
        self.assertFalse('diagnostico' in self.public)
        self.assertFalse(any(x['servico'] in ('seguranca','qualidade','equipamento','ambiental') for x in self.public['referencias_eventos']))
        self.assertFalse(any(x['validacao_relato']=='pendente_esclarecimento' for x in self.public['referencias_eventos']))
    def test_aggregates(self):
        q=self.internal['base_quantitativa']
        self.assertEqual((q['estacas_previstas'],q['estacas_execucao_registrada'],q['estacas_concretagem_identificada']), (292,145,111))
        self.assertEqual((q['blocos_concluidos_registrados'],q['pilares_integralmente_concretados_registrados'],q['longarinas_concretadas_registradas']), (2,6,3))
        self.assertEqual(q['prelajes_incrementais_novembro'],218)
        self.assertIsNone(q['prelajes_estoque_total'])
    def test_axis_totals(self):
        s={x['id']:x for x in self.internal['eixos']}
        self.assertEqual((s['E07']['estacas_execucao_registrada'],s['E07']['estacas_concretagem_identificada']), (19,4))
        self.assertEqual((s['E08']['estacas_execucao_registrada'],s['E08']['estacas_concretagem_identificada']), (13,11))
        self.assertEqual((s['E09']['estacas_previstas'],s['E09']['estacas_execucao_registrada'],s['E09']['estacas_concretagem_identificada']), (24,25,8))
        self.assertEqual(s['E09']['excedente_execucao_sobre_projeto'],1)
    def test_no_unjustified_technical_approvals(self):
        for x in self.internal['eixos']:
            self.assertEqual(x['controle_tecnologico']['situacao'],'nao_avaliado')
            self.assertEqual(x['hold_point']['situacao'],'nao_configurado')
            self.assertIsNone(x['medicao']['quantidade_apta'])
        self.assertEqual(len(self.internal['controles_formais']['rnc']),0)
        self.assertEqual(len(self.internal['controles_formais']['rfi']),0)
    def test_e03_pillars_partial_only(self):
        els=self.internal['elementos_individualizados']
        self.assertEqual({e['id'] for e in els},{'E03-P03','E03-P04'})
        self.assertTrue(all(not e['execucao_integral_comprovada'] for e in els))
    def test_no_fake_schedule_or_payment(self):
        g=self.internal['gestao_contratual']
        self.assertIsNone(g['idp_spi'])
        self.assertIsNone(g['linha_base_cronograma_aprovada_id'])
        self.assertIsNone(g['medicao_financeira_vigente'])
    def test_reject_overcount(self):
        bad=copy.deepcopy(self.internal)
        bad['eixos'][8]['estacas_execucao_registrada']=24
        with self.assertRaises(ValueError):validate(bad,SOURCE_ROOT)
    def test_reject_forged_approval(self):
        bad=copy.deepcopy(self.internal)
        bad['eixos'][8]['controle_tecnologico']['situacao']='conforme'
        with self.assertRaises(ValueError):validate(bad,SOURCE_ROOT)
    def test_reject_changed_raw_event_status(self):
        bad=copy.deepcopy(self.internal)
        bad['referencias_eventos'][0]['validacao_relato']='pendente_esclarecimento'
        with self.assertRaises(ValueError):validate(bad,SOURCE_ROOT)
    def test_reject_synthetic_rnc(self):
        bad=copy.deepcopy(self.internal)
        bad['alertas_derivados'][0]['rnc_formal']=True
        with self.assertRaises(ValueError):validate(bad,SOURCE_ROOT)
    def test_reject_public_with_audit(self):
        bad=copy.deepcopy(self.public)
        bad['diagnostico']={'registros_totais':60}
        with self.assertRaises((ValueError,ValidationError)):validate(bad,SOURCE_ROOT)
    def test_require_all_source_hashes(self):
        bad=copy.deepcopy(self.internal)
        bad['origem']['arquivos_sha256'][0]['sha256']='f'*64
        with self.assertRaises(ValueError):validate(bad,SOURCE_ROOT)
    def test_outputs_deterministic(self):
        self.assertEqual(self.internal,get_snapshot(SOURCE_ROOT,'interno',AUDIT))
        self.assertEqual(self.public,get_snapshot(SOURCE_ROOT,'publico'))

if __name__=='__main__':unittest.main()