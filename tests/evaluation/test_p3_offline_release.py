from evaluation.p3.admission import deny_before_evaluation

def test_unavailable_receipt_authority_is_external_impasse_not_fallback():
 result=deny_before_evaluation(receipt_log=None,lock=None,reason='receipt-writer-unavailable')
 assert result=={'outcome':'impasse','reason':'receipt-writer-unavailable','worker_launch':False}
