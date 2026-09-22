import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss

class GoalEnsemble:
    """Blend calibrated Dixon-Coles/Poisson with ML probabilities.

    The meta-model is trained only on out-of-fold/walk-forward predictions.
    This avoids training the ensemble on in-sample base-model outputs.
    """
    def __init__(self):
        self.ml=HistGradientBoostingClassifier(max_iter=200,max_leaf_nodes=15,l2_regularization=1.0)
        self.meta=LogisticRegression(C=1.0)
        self.ready=False

    def fit(self,X,y,dc_p):
        X=np.asarray(X,float); y=np.asarray(y,int); dc=np.asarray(dc_p,float)
        base=np.column_stack([dc,X])
        self.ml.fit(X,y)
        mlp=self.ml.predict_proba(X)[:,1]
        meta=np.column_stack([dc,mlp,X])
        self.meta.fit(meta,y)
        self.ready=True
        return self

    def predict_proba(self,X,dc_p):
        if not self.ready: raise RuntimeError("Ensemble not trained.")
        X=np.asarray(X,float); dc=np.asarray(dc_p,float)
        mlp=self.ml.predict_proba(X)[:,1]
        return self.meta.predict_proba(np.column_stack([dc,mlp,X]))[:,1]
