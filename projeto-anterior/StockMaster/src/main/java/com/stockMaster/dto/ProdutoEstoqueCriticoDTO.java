package com.stockMaster.dto;

public record ProdutoEstoqueCriticoDTO(
        Long id,
        String nome,
        Integer quantidade,
        Integer estoqueMinimo
) {
}
