import numpy as np
import time
from math import pi
import maxvol as mv
import copy
from scipy.special import erf
from tucker import *




def cross_multifun(X, delta_cross, fun, (r1_0, r2_0, r3_0) = (4, 4, 4)):

    # For X = [X_1,...,X_d], where X_i - tensors in the Tucker format
    # cross_func computes func(X) == func(X_1,...,X_d) in the Tucker format by using cross3d
    #
    # delta_cross - accuracy for cross3D
    # (r1_0, r2_0, r3_0) - number of computed columns on each iteration of cross3d. May be used to improve time performing.
    
    M = X[0].n[0]
    N = int((M+1)/2)

    d = len(X)

    r1 = r1_0
    r2 = r2_0
    r3 = r3_0

    GG = np.zeros((r1,r2,r3), dtype=np.complex128)

    U1 = np.zeros((M, r1), dtype=np.complex128)
    U2 = np.zeros((M, r2), dtype=np.complex128)
    U3 = np.zeros((M, r3), dtype=np.complex128)

    U1[:N,:] = np.random.random((N,r1))
    U2[:N,:] = np.random.random((N,r2))
    U3[:N,:] = np.random.random((N,r3))

    U1, R = np.linalg.qr(U1)
    U2, R = np.linalg.qr(U2)
    U3, R = np.linalg.qr(U3)

    row_order_U1 = mv.maxvol(U1)
    row_order_U2 = mv.maxvol(U2)
    row_order_U3 = mv.maxvol(U3)

    eps_cross = 1

    A = [None]*d
    
    for alpha in xrange(d):
        A[alpha] = np.dot(X[alpha].G, np.transpose(X[alpha].U[2][row_order_U3,:]))
        A[alpha] = np.dot(np.transpose(A[alpha], [2,0,1]), np.transpose(X[alpha].U[1][row_order_U2,:]))
        A[alpha] = np.dot(np.transpose(A[alpha], [0,2,1]), np.transpose(X[alpha].U[0][row_order_U1,:]))
        A[alpha] = np.transpose(A[alpha], [2,1,0])
    Ar = fun(A)
    
    A1 = np.reshape(Ar, [r1,-1], order='f')
    A1 = np.transpose(A1)
    column_order_U1 = mv.maxvol(A1)
    A1_11 = A1[column_order_U1, :]


    A2 = np.reshape(np.transpose(Ar, [1,0,2]), [r2,-1], order='f')
    A2 = np.transpose(A2)
    column_order_U2 = mv.maxvol(A2)
    A2_11 = A2[column_order_U2, :]


    A3 = np.reshape(np.transpose(Ar, [2,0,1]), [r3,-1], order='f')
    A3 = np.transpose(A3)
    column_order_U3 = mv.maxvol(A3)
    A3_11 = A3[column_order_U3, :]


    u1 = np.zeros((M, r1), dtype=np.complex128)
    for i in xrange(r1):
        for alpha in xrange(d):
            k1_order, j1_order = mod(column_order_U1[i], r2)
            A[alpha] = np.dot(X[alpha].G,np.transpose(X[alpha].U[2][row_order_U3[k1_order]:row_order_U3[k1_order]+1,:]))
            A[alpha] = np.dot(np.transpose(A[alpha], [2,0,1]), np.transpose(X[alpha].U[1][row_order_U2[j1_order]:row_order_U2[j1_order]+1,:]))
            A[alpha] = np.dot(np.transpose(A[alpha], [0,2,1]), np.transpose(X[alpha].U[0]))
            A[alpha] = np.transpose(A[alpha], [2,1,0])[:, 0, 0]
        u1[:,i] = fun(A)


    u2 = np.zeros((M, r2), dtype=np.complex128)
    for j in xrange(r2):
        for alpha in xrange(d):
            k1_order, i1_order = mod(column_order_U2[j], r1)
            A[alpha] = np.dot(X[alpha].G, np.transpose(X[alpha].U[2][row_order_U3[k1_order]:row_order_U3[k1_order]+1,:]))
            A[alpha] = np.dot(np.transpose(A[alpha], [2,1,0]),np.transpose(X[alpha].U[0][row_order_U1[i1_order]:row_order_U1[i1_order]+1,:]))
            A[alpha] = np.dot(np.transpose(A[alpha], [0,2,1]),np.transpose(X[alpha].U[1]))
            A[alpha] = np.transpose(A[alpha], [1,2,0])[0, :, 0]
        u2[:,j] = fun(A)


    u3 = np.zeros((M, r3), dtype=np.complex128)
    for k in xrange(r3):
        for alpha in xrange(d):
            j1_order, i1_order = mod(column_order_U3[k], r1)
            A[alpha] = np.dot(np.transpose(X[alpha].G, [2,1,0]),np.transpose(X[alpha].U[0][row_order_U1[i1_order]:row_order_U1[i1_order]+1,:]))
            A[alpha] = np.dot(np.transpose(A[alpha], [0,2,1]),np.transpose(X[alpha].U[1][row_order_U2[j1_order]:row_order_U2[j1_order]+1,:]))
            A[alpha] = np.dot(np.transpose(A[alpha], [1,2,0]),np.transpose(X[alpha].U[2]))[0,0,:]
        u3[:,k] = fun(A)


    U1_hat = np.linalg.solve(U1[row_order_U1, :].T, U1.T).T
    U2_hat = np.linalg.solve(U2[row_order_U2, :].T, U2.T).T
    U3_hat = np.linalg.solve(U3[row_order_U3, :].T, U3.T).T

    UU1, ind_update_1 = column_update(U1_hat, u1, row_order_U1)
    UU2, ind_update_2 = column_update(U2_hat, u2, row_order_U2)
    UU3, ind_update_3 = column_update(U3_hat, u3, row_order_U3)

    U1 = np.concatenate((U1, u1), 1)
    U2 = np.concatenate((U2, u2), 1)
    U3 = np.concatenate((U3, u3), 1)

    A1_12 = np.zeros((r1, r1_0),dtype=np.complex128)
    for ii in xrange(r1):
        for alpha in xrange(d):
            k1_order, j1_order = mod(column_order_U1[ii], r2)
            A[alpha] = np.dot(X[alpha].G, np.transpose(X[alpha].U[2][row_order_U3[k1_order]:row_order_U3[k1_order]+1,:]))
            A[alpha] = np.dot(np.transpose(A[alpha], [2,0,1]),np.transpose(X[alpha].U[1][row_order_U2[j1_order]:row_order_U2[j1_order]+1,:]))
            A[alpha] = np.dot(np.transpose(A[alpha], [0,2,1]),np.transpose(X[alpha].U[0][ind_update_1, :]))
            A[alpha] = np.transpose(A[alpha], [2,1,0])[:,0,0]
        A1_12[ii,:] = fun(A)


    A2_12 = np.zeros((r2, r2_0),dtype=np.complex128)
    for ii in xrange(r2):
        for alpha in xrange(d):
            k1_order, i1_order = mod(column_order_U2[ii], r1)
            A[alpha] = np.dot(X[alpha].G, np.transpose(X[alpha].U[2][row_order_U3[k1_order]:row_order_U3[k1_order]+1,:]))
            A[alpha] = np.dot(np.transpose(A[alpha], [2,1,0]), np.transpose(X[alpha].U[0][row_order_U1[i1_order]:row_order_U1[i1_order]+1,:]))
            A[alpha] = np.dot(np.transpose(A[alpha], [0,2,1]), np.transpose(X[alpha].U[1][ind_update_2, :]))
            A[alpha] = np.transpose(A[alpha], [1,2,0])[0,:,0]
        A2_12[ii, :] = fun(A)


    A3_12 = np.zeros((r3, r3_0),dtype=np.complex128)
    for ii in xrange(r3):
        for alpha in xrange(d):
            j1_order, i1_order = mod(column_order_U3[ii], r1)
            A[alpha] = np.dot(np.transpose(X[alpha].G, [2,1,0]),np.transpose(X[alpha].U[0][row_order_U1[i1_order]:row_order_U1[i1_order]+1,:]))
            A[alpha] = np.dot(np.transpose(A[alpha], [0,2,1]),np.transpose(X[alpha].U[1][row_order_U2[j1_order]:row_order_U2[j1_order]+1,:]))
            A[alpha] = np.dot(np.transpose(A[alpha], [1,2,0]),np.transpose(X[alpha].U[2][ind_update_3, :]))[0,0,:]
        A3_12[ii, :] = fun(A)


    r1 = r1+r1_0
    r2 = r2+r2_0
    r3 = r3+r3_0



    while True:
    
        for alpha in xrange(d):
            A[alpha] = np.dot(np.transpose(X[alpha].G, [2,1,0]), np.transpose(X[alpha].U[0][ind_update_1,:]))
            A[alpha] = np.dot(np.transpose(A[alpha], [0,2,1]), np.transpose(X[alpha].U[1][row_order_U2,:]))
            A[alpha] = np.dot(np.transpose(A[alpha], [1,2,0]), np.transpose(X[alpha].U[2][row_order_U3,:]))
        Ar_1 = np.concatenate((Ar, fun(A)), 0)

        row_order_U1 = np.concatenate((row_order_U1, ind_update_1))

        for alpha in xrange(d):
            A[alpha] = np.dot(np.transpose(X[alpha].G, [0,2,1]), np.transpose(X[alpha].U[1][ind_update_2,:]))
            A[alpha] = np.dot(np.transpose(A[alpha], [0,2,1]), np.transpose(X[alpha].U[2][row_order_U3,:]))
            A[alpha] = np.dot(np.transpose(A[alpha], [2,1,0]), np.transpose(X[alpha].U[0][row_order_U1,:]))
            A[alpha] = np.transpose(A[alpha], [2,1,0])
        Ar_2 = np.concatenate((Ar_1, fun(A)), 1)

        row_order_U2 = np.concatenate((row_order_U2, ind_update_2))

        for alpha in xrange(d):
            A[alpha] = np.dot(X[alpha].G, np.transpose(X[alpha].U[2][ind_update_3,:]))
            A[alpha] = np.dot(np.transpose(A[alpha], [2,0,1]),np.transpose(X[alpha].U[1][row_order_U2,:]))
            A[alpha] = np.dot(np.transpose(A[alpha], [0,2,1]),np.transpose(X[alpha].U[0][row_order_U1,:]))
            A[alpha] = np.transpose(A[alpha], [2,1,0])
        Ar = np.concatenate((Ar_2, fun(A)), 2)

        row_order_U3 = np.concatenate((row_order_U3, ind_update_3))



        A1 = np.reshape(Ar, [r1,-1], order='f')
        A1 = np.transpose(A1)
        column_order_update_U1 = mv.maxvol( schur_comp(A1, A1_11, A1_12) )
        r1_0 = len(column_order_update_U1)

        A2 = np.reshape(np.transpose(Ar, [1,0,2]), [r2,-1], order='f')
        A2 = np.transpose(A2)
        column_order_update_U2 = mv.maxvol( schur_comp(A2, A2_11, A2_12) )
        r2_0 = len(column_order_update_U2)

        A3 = np.reshape(np.transpose(Ar, [2,0,1]), [r3,-1], order='f')
        A3 = np.transpose(A3)
        column_order_update_U3 = mv.maxvol( schur_comp(A3, A3_11, A3_12) )
        r3_0 = len(column_order_update_U3)



        u1_approx = np.zeros((M, r1_0), dtype=np.complex128)
        u1 = np.zeros((M, r1_0), dtype=np.complex128)
        for i in xrange(r1_0):
            for alpha in xrange(d):
                k1_order, j1_order = mod(column_order_update_U1[i], r2)
                A[alpha] = np.dot(X[alpha].G, np.transpose(X[alpha].U[2][row_order_U3[k1_order]:row_order_U3[k1_order]+1,:]))
                A[alpha] = np.dot(np.transpose(A[alpha], [2,0,1]),np.transpose(X[alpha].U[1][row_order_U2[j1_order]:row_order_U2[j1_order]+1,:]))
                A[alpha] = np.dot(np.transpose(A[alpha], [0,2,1]),np.transpose(X[alpha].U[0]))
                A[alpha] = np.transpose(A[alpha], [2,1,0])[:,0,0]
            u1[:,i] = fun(A)

            u1_approx_i = np.dot(Ar, np.transpose(UU3[row_order_U3[k1_order]:row_order_U3[k1_order]+1,:]))
            u1_approx_i = np.dot(np.transpose(u1_approx_i,[2,0,1]),np.transpose(UU2[row_order_U2[j1_order]:row_order_U2[j1_order]+1,:]))
            u1_approx_i = np.dot(np.transpose(u1_approx_i,[0,2,1]),np.transpose(UU1))
            u1_approx_i = np.transpose(u1_approx_i,[2,1,0])
            u1_approx[:,i] = u1_approx_i[:, 0, 0]


        u2_approx = np.zeros((M, r2_0), dtype=np.complex128)
        u2 = np.zeros((M, r2_0), dtype=np.complex128)
        for j in xrange(r2_0):
            for alpha in xrange(d):
                k1_order, i1_order = mod(column_order_update_U2[j], r1)
                A[alpha] = np.dot(X[alpha].G, np.transpose(X[alpha].U[2][row_order_U3[k1_order]:row_order_U3[k1_order]+1,:]))
                A[alpha] = np.dot(np.transpose(A[alpha], [2,1,0]), np.transpose(X[alpha].U[0][row_order_U1[i1_order]:row_order_U1[i1_order]+1,:]))
                A[alpha] = np.dot(np.transpose(A[alpha], [0,2,1]), np.transpose(X[alpha].U[1]))
                A[alpha] = np.transpose(A[alpha], [1,2,0])[0,:,0]
            u2[:,j] = fun(A)

            u2_approx_j = np.dot(Ar,np.transpose(UU3[row_order_U3[k1_order]:row_order_U3[k1_order]+1,:]))
            u2_approx_j = np.dot(np.transpose(u2_approx_j,[2,1,0]),np.transpose(UU1[row_order_U1[i1_order]:row_order_U1[i1_order]+1,:]))
            u2_approx_j = np.dot(np.transpose(u2_approx_j,[0,2,1]),np.transpose(UU2))
            u2_approx[:,j] = u2_approx_j[0, 0, :]

        u3_approx = np.zeros((M, r3_0), dtype=np.complex128)
        u3 = np.zeros((M, r3_0), dtype=np.complex128)
        for k in xrange(r3_0):
            for alpha in xrange(d):
                j1_order, i1_order = mod(column_order_update_U3[k], r1)
                A[alpha] = np.dot(np.transpose(X[alpha].G, [2,1,0]),np.transpose(X[alpha].U[0][row_order_U1[i1_order]:row_order_U1[i1_order]+1,:]))
                A[alpha] = np.dot(np.transpose(A[alpha], [0,2,1]),np.transpose(X[alpha].U[1][row_order_U2[j1_order]:row_order_U2[j1_order]+1,:]))
                A[alpha] = np.dot(np.transpose(A[alpha], [1,2,0]),np.transpose(X[alpha].U[2]))[0,0,:]
            u3[:,k] = fun(A)

            u3_approx_k = np.dot(np.transpose(Ar,[2,1,0]),np.transpose(UU1[row_order_U1[i1_order]:row_order_U1[i1_order]+1,:]))
            u3_approx_k = np.dot(np.transpose(u3_approx_k,[0,2,1]),np.transpose(UU2[row_order_U2[j1_order]:row_order_U2[j1_order]+1,:]))
            u3_approx_k = np.dot(np.transpose(u3_approx_k,[1,2,0]),np.transpose(UU3))
            u3_approx[:,k] = u3_approx_k[0, 0, :]


        eps_cross = 1./3*(  np.linalg.norm(u1_approx - u1)/ np.linalg.norm(u1) +
                            np.linalg.norm(u2_approx - u2)/ np.linalg.norm(u2) +
                            np.linalg.norm(u3_approx - u3)/ np.linalg.norm(u3)   )
        #print 'relative accuracy = %s' % (eps_cross), 'ranks = %s' % r1, r2, r3

        if eps_cross < delta_cross:
            break

        #print np.linalg.norm( full(G, U1, U2, U3) - C_toch )/np.linalg.norm(C_toch)


        UU1, ind_update_1 = column_update(UU1, u1, row_order_U1)
        UU2, ind_update_2 = column_update(UU2, u2, row_order_U2)
        UU3, ind_update_3 = column_update(UU3, u3, row_order_U3)


        U1 = np.concatenate((U1, u1), 1)
        U2 = np.concatenate((U2, u2), 1)
        U3 = np.concatenate((U3, u3), 1)


        A1_11 = np.concatenate((A1_11, A1_12), 1)
        A1_11 = np.concatenate((A1_11, A1[column_order_update_U1,:]) )

        A2_11 = np.concatenate((A2_11, A2_12), 1)
        A2_11 = np.concatenate((A2_11, A2[column_order_update_U2,:]) )

        A3_11 = np.concatenate((A3_11, A3_12), 1)
        A3_11 = np.concatenate((A3_11, A3[column_order_update_U3,:]) )

        A1_12 = U1[ind_update_1, r1_0:].T
        A2_12 = U2[ind_update_2, r2_0:].T
        A3_12 = U3[ind_update_3, r3_0:].T

        r1 = r1+r1_0
        r2 = r2+r2_0
        r3 = r3+r3_0


        #print r1, r2, r3


    #print r1, r2, r3
    U1, R1 = np.linalg.qr(UU1)
    U2, R2 = np.linalg.qr(UU2)
    U3, R3 = np.linalg.qr(UU3)


    GG = np.dot(np.transpose(Ar,[2,1,0]),np.transpose(R1))
    GG = np.dot(np.transpose(GG,[0,2,1]),np.transpose(R2))
    GG = np.transpose(GG,[1,2,0])
    G = np.dot(GG,np.transpose(R3))

    G_Tucker = tensor(G, delta_cross)
    #print 'ranks after rounding = %s' % G_Tucker.r[0], G_Tucker.r[1], G_Tucker.r[2]


    fun = tensor()
    fun.G = G_Tucker.G
    fun.U[0] = np.dot(U1, G_Tucker.U[0])
    fun.U[1] = np.dot(U2, G_Tucker.U[1])
    fun.U[2] = np.dot(U3, G_Tucker.U[2])
    fun.r =  G_Tucker.r
    fun.n = (M, M, M)
   
    #print 'cross ending'
    return fun



def schur_comp(A, A11, A12):
    r, r0 = A12.shape
    R = r + r0
    
    #print np.linalg.solve(A11.T, A[:,:r].T).T
    S_hat = np.zeros((R,r0), dtype=np.complex128)
    
    S_hat[:r, :] = np.dot(np.linalg.pinv(A11), -A12)#np.linalg.solve(A11, -A12)
    S_hat[r:, :] = np.identity(r0)
    
    #print A[:,:]
    #uu, ss, vv = np.linalg.svd(np.dot(A, S_hat))
    #'ss:', ss
    
    
    Q, R = np.linalg.qr(np.dot(A, S_hat))
    #Q , trash1, trash2 = round_matrix(np.dot(A, S_hat), delta_tucker)
    
    return Q

def mod(X,Y):
    return int(X/Y), X%Y

def maxvol_update(A, ind):
    # finds new r0 good rows
    # [ A11 A12]
    # [ A21 A22] => S = A22 - A21 A11^(-1) A12
    
    N, R = A.shape
    r = len(ind)
    r0 = R - r
    
    S_hat = np.zeros((R, r0),dtype=np.complex128)
    
    S_hat[:r, :] = np.linalg.solve(A[ind, :r], -A[ind, r:])
    S_hat[r:, :] = np.identity(r0)
    Q, R = np.linalg.qr(np.dot(A, S_hat))
    
    ind_update = mv.maxvol(Q)
    
    
    return ind_update


def column_update(UU, u, ind):
    
    S = u - np.dot(UU, u[ind,:])
    ind_add = mv.maxvol(S)
    
    SS = np.dot(np.linalg.pinv(S[ind_add, :].T), S.T).T # WARNING! pinv instead of solve!
    #np.linalg.solve(S[ind_add, :].T, S.T).T#np.dot(np.linalg.pinv(S[ind_add, :].T), S.T).T
    
    U1 = UU - np.dot(SS, UU[ind_add])
    U2 = SS
    
    return np.concatenate((U1, U2), 1), ind_add

