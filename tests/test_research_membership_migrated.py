import pytest
from domains.engine_provenance import engine_preamble
from scripts.ocelot_research_formula import FormulaTranslationError
from scripts.ocelot_research_membership import translate_membership


def test_real_latex_shape_translates_and_executes():
    engine_preamble()
    from substrate_rs import Substrate
    model = translate_membership(r'\epsilon,\mu\in\{0,1\}')
    engine = Substrate()
    assert engine._inner.evaluate(model.term, {'epsilon': 0, 'mu': 1}) is True
    assert engine._inner.evaluate(model.term, {'epsilon': 2, 'mu': 1}) is False
    assert model.variable_sorts == {'epsilon': 'int', 'mu': 'int'}


@pytest.mark.parametrize('text', [r'x\in\mathbb{N}', r'x\in\{0,True\}', r'\foo\in\{0,1\}', r'x\in\{y,1\}', r'x\notin\{0,1\}', r'x,x\in\{0,1\}'])
def test_unbounded_mixed_unknown_and_ambiguous_forms_refused(text):
    with pytest.raises(FormulaTranslationError):
        translate_membership(text)


def test_natural_membership_requires_explicit_zero_or_one_convention():
    with pytest.raises(FormulaTranslationError, match='explicit minimum'):
        translate_membership(r'm,n\in\NN')
    engine_preamble()
    from substrate_rs import Substrate
    zero = translate_membership(r'm,n\in\NN', natural_minimum=0)
    one = translate_membership(r'm,n\in\NN', natural_minimum=1)
    s = Substrate()
    assert s._inner.evaluate(zero.term, {'m': 0, 'n': 1}) is True
    assert s._inner.evaluate(one.term, {'m': 0, 'n': 1}) is False
    assert any('i64' in x for x in zero.residuals)
